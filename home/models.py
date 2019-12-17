import base64
import hashlib
import os
import pickle
import re
import socket
import ujson
from itertools import count
from time import sleep

import mutagen
import requests
import transmissionrpc
from whatapi import WhatAPI

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.functional import cached_property

from WhatManager2 import settings
from WhatManager2.throttling import Throttler
from WhatManager2.utils import match_properties, copy_properties, norm_t_torrent, html_unescape, \
    get_artists
from home.info_holder import InfoHolder
from what_meta.models import WhatTorrentGroup
from pyquery.pyquery import PyQuery


class TorrentAlreadyAddedException(Exception):
    pass


class TrackerAccount(models.Model):
    ZONE_RED = 'redacted.ch'
    ZONE_BIBLIOTIK = 'bibliotik.me'
    ZONE_MYANONAMOUSE = 'myanonamouse.net'

    ZONES = [
        (ZONE_RED, 'Redacted'),
        (ZONE_BIBLIOTIK, 'Bibliotik'),
        (ZONE_MYANONAMOUSE, 'MyAnonaMouse'),
    ]

    zone = models.CharField(choices=ZONES, max_length=20)
    user_id = models.IntegerField(blank=True, null=True)
    username = models.CharField(max_length=40, blank=True, null=True)
    password = models.CharField(max_length=256, blank=True, null=True)
    api_key = models.CharField(max_length=256, blank=True, null=True)
    announce_url = models.URLField(blank=True, null=True)
    snapshot_interval = models.IntegerField(default=600)
    min_ratio = models.DecimalField(max_digits=4, decimal_places=2, default=1.3)
    sync_files = models.BooleanField(default=False)
    download_location = models.OneToOneField('DownloadLocation', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return '{} Account ({})'.format([z for z in self.ZONES if z[0] == self.zone][0][1], self.username)

    @classmethod
    def get_red(cls):
        return TrackerAccount.objects.get(zone=TrackerAccount.ZONE_RED)

    @classmethod
    def get_bib(cls):
        return TrackerAccount.objects.get(zone=TrackerAccount.ZONE_BIBLIOTIK)

    @classmethod
    def get_mam(cls):
        return TrackerAccount.objects.get(zone=TrackerAccount.ZONE_MYANONAMOUSE)


class ResourceAccount(models.Model):
    SITES = [
        ('PI', 'PTPIMG'),
        ('TI', 'Tidal'),
        ('QO', 'Qobuz'),
    ]

    site = models.CharField(choices=SITES, max_length=2)
    username = models.CharField(max_length=40, blank=True, null=True)
    password = models.CharField(max_length=256, blank=True, null=True)
    session_id = models.CharField(max_length=256, blank=True, null=True)
    preferred = models.BooleanField(default=False)

    def __str__(self):
        return '{} Account ({}){}'.format([
            s for s in self.SITES if s[0] == self.site][0][1], \
            self.username, ' [Preferred]' if self.preferred else '')

    @classmethod
    def get_ptpimg(cls):
        ResourceAccount.objects.get(site='PI')

    @classmethod
    def get_tidal(cls):
        ResourceAccount.objects.get(site='TI')

    @classmethod
    def get_qobuz(cls):
        ResourceAccount.objects.get(site='QO')


class ReplicaSet(models.Model):
    zone = models.CharField(choices=TrackerAccount.ZONES, max_length=32)
    name = models.TextField()

    def __str__(self):
        return 'ReplicaSet({0}, {1})'.format(self.zone, self.name)

    @property
    def is_master(self):
        return self.name == 'master'

    @property
    def torrent_count(self):
        return sum(i.torrent_count for i in self.transinstance_set.all())

    @property
    def torrents_size(self):
        return sum(filter(None, (i.torrents_size for i in self.transinstance_set.all())))

    def get_preferred_instance(self):
        return sorted(self.transinstance_set.all(), key=lambda x: x.torrent_count)[0]

    @classmethod
    def get_what_master(cls):
        return cls.objects.get(zone=TrackerAccount.ZONE_RED, name='master')

    @classmethod
    def get_bibliotik_master(cls):
        return cls.objects.get(zone=TrackerAccount.ZONE_BIBLIOTIK, name='master')

    @classmethod
    def get_myanonamouse_master(cls):
        return cls.objects.get(zone=TrackerAccount.ZONE_MYANONAMOUSE, name='master')


class DownloadLocation(models.Model):
    path = models.TextField()

    def __str__(self):
        return 'DownloadLocation({0}, {1})'.format(self.zone, self.path)

    @cached_property
    def disk_space(self):
        stat = os.statvfs(self.path)
        return {
            'free': stat.f_bfree * stat.f_bsize,
            'used': (stat.f_blocks - stat.f_bfree) * stat.f_bsize,
            'total': stat.f_blocks * stat.f_bsize
        }

    @cached_property
    def free_space_percent(self):
        return float(self.disk_space['free']) / self.disk_space['total']

    @cached_property
    def zone(self):
        try:
            return self.trackeraccount.zone
        except TrackerAccount.DoesNotExist as e:
            return 'zoneless'

    @classmethod
    def get_bibliotik_preferred(cls):
        return DownloadLocation.objects.get(
            zone=TrackerAccount.ZONE_BIBLIOTIK,
            preferred=True,
        )

    @classmethod
    def get_myanonamouse_preferred(cls):
        return DownloadLocation.objects.get(
            zone=TrackerAccount.ZONE_MYANONAMOUSE,
            preferred=True,
        )

    @cached_property
    def torrent_count(self):
        replica_sets = ReplicaSet.objects.filter(name='master')
        instances = TransInstance.objects.filter(replica_set__in=replica_sets)
        return (
            self.transtorrent_set.filter(instance__in=instances).count() +
            self.bibliotiktranstorrent_set.filter(instance__in=instances).count()
        )

    @classmethod
    def get_by_full_path(cls, full_path):
        for d in DownloadLocation.objects.all():
            if full_path.startswith(d.path):
                return d
        return None


class TransInstance(models.Model):
    class Meta:
        permissions = (
            ('view_transinstance_stats', 'Can view current Transmission stats.'),
            ('run_checks', 'Can run the validity checks.'),
        )

    replica_set = models.ForeignKey(ReplicaSet, on_delete=models.CASCADE)
    name = models.TextField(default='red_1')
    host = models.TextField(default='whatmanager2_trans_red_1')
    port = models.IntegerField(default=9091)
    peer_port = models.IntegerField(default=21413)
    username = models.TextField(default=os.getenv('WM_USER', 'transmission'))
    password = models.TextField(default=settings.TRANSMISSION_PASSWORD)

    def __str__(self):
        return 'TransInstance {0}({1}@{2}:{3})'.format(self.name, self.username,
                                                        self.host, self.port)

    def full_description(self):
        return 'TransInstance {0}(replica_set={1}, host={2}, rpc_port={3}, ' \
               'peer_port={4}, username={5}, password={6})' \
            .format(self.name, self.replica_set, self.host, self.port, self.peer_port,
                    self.username, self.password)

    @property
    def client(self):
        if not hasattr(self, '_client'):
            self._client = transmissionrpc.Client(address=self.host, port=self.port,
                                                  user=self.username, password=self.password)
        return self._client

    @property
    def torrent_count(self):
        if self.replica_set.zone == TrackerAccount.ZONE_RED:
            return self.transtorrent_set.count()
        elif self.replica_set.zone == TrackerAccount.ZONE_BIBLIOTIK:
            return self.bibliotiktranstorrent_set.count()

    @property
    def torrents_size(self):
        if self.replica_set.zone == TrackerAccount.ZONE_RED:
            return self.transtorrent_set.aggregate(Sum('torrent_size'))['torrent_size__sum']
        elif self.replica_set.zone == TrackerAccount.ZONE_BIBLIOTIK:
            return self.bibliotiktranstorrent_set.aggregate(
                Sum('torrent_size'))['torrent_size__sum']

    def get_t_torrents(self, arguments):
        torrents = []
        locations = DownloadLocation.objects.filter(zone=self.replica_set.zone)
        if 'downloadDir' not in arguments:
            arguments.append('downloadDir')
        for t in self.client.get_torrents(arguments=arguments):
            if any([l for l in locations if t.downloadDir.startswith(l.path)]):
                norm_t_torrent(t)
                torrents.append(t)
        return torrents

    def get_t_torrents_by_hash(self, arguments):
        torrents = {}
        for t in self.get_t_torrents(arguments):
            torrents[t.hashString] = t
        return torrents

    def get_m_torrents_by_hash(self):
        torrents = {}
        for t in self.transtorrent_set.all():
            existing = torrents.get(t.info_hash)
            if existing and t.what_torrent_id == existing.what_torrent_id:
                t.delete()
                continue
            torrents[t.info_hash] = t
        return torrents

    def get_b_torrents_by_hash(self):
        torrents = {}
        for t in self.bibliotiktranstorrent_set.all():
            existing = torrents.get(t.info_hash)
            if existing and t.bibliotik_torrent_id == existing.bibliotik_torrent_id:
                t.delete()
                continue
            torrents[t.info_hash] = t
        return torrents

    def get_mam_torrents_by_hash(self):
        torrents = {}
        for t in self.mamtranstorrent_set.all():
            existing = torrents.get(t.info_hash)
            if existing and t.mam_torrent_id == existing.mam_torrent_id:
                t.delete()
                continue
            torrents[t.info_hash] = t
        return torrents


class WhatFulltext(models.Model):
    info = models.TextField()
    more_info = models.TextField()

    def get_info(self, what_torrent):
        info = ujson.loads(what_torrent.info)

        info_text = []
        info_text.append(str(info['group']['id']))
        info_text.append(info['group']['recordLabel'])
        info_text.append(info['group']['name'])
        info_text.append(info['group']['catalogueNumber'])
        if info['group']['musicInfo']:
            for type, artists in list(info['group']['musicInfo'].items()):
                if artists:
                    artist_names = [a['name'] for a in artists]
                    info_text.append(', '.join(artist_names))
        info_text.append(str(info['group']['year']))

        info_text.append(str(info['torrent']['id']))
        info_text.append(str(info['torrent']['remasterYear']))
        info_text.append(info['torrent']['filePath'])
        info_text.append(info['torrent']['remasterCatalogueNumber'])
        info_text.append(info['torrent']['remasterRecordLabel'])
        info_text.append(info['torrent']['remasterTitle'])

        info_text = '\r\n'.join(info_text)
        info_text = html_unescape(info_text)
        return info_text

    def match(self, what_torrent):
        return (
            self.get_info(what_torrent) == self.info and
            what_torrent.info == self.more_info
        )

    def update(self, what_torrent):
        self.info = self.get_info(what_torrent)
        self.more_info = what_torrent.info
        self.save()

    def __str__(self):
        return 'WhatFulltext id={0}'.format(self.id)


class WhatTorrent(models.Model, InfoHolder):
    class Meta:
        permissions = (
            ('download_whattorrent', 'Can download and play torrents.'),
        )

    info_hash = models.CharField(max_length=40, db_index=True)
    torrent_file = models.TextField()
    torrent_file_name = models.TextField()
    retrieved = models.DateTimeField(db_index=True)
    info = models.TextField()
    tags = models.TextField()
    added_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    torrent_group = models.ForeignKey('what_meta.WhatTorrentGroup', null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            try:
                if int(self.info_category_id) == 1:
                    self.torrent_group = WhatTorrentGroup.update_if_newer(
                        self.info_loads['group']['id'], self.retrieved, self.info_loads['group'])
            except Exception:
                pass
            super(WhatTorrent, self).save(*args, **kwargs)
        try:
            what_fulltext = WhatFulltext.objects.get(id=self.id)
            if not what_fulltext.match(self):
                what_fulltext.update(self)
        except WhatFulltext.DoesNotExist:
            what_fulltext = WhatFulltext(id=self.id)
            what_fulltext.update(self)

    def delete(self, *args, **kwargs):
        try:
            WhatFulltext.objects.get(id=self.id).delete()
        except WhatFulltext.DoesNotExist:
            pass
        super(WhatTorrent, self).delete(*args, **kwargs)

    def __str__(self):
        return 'WhatTorrent id={0} hash={1}'.format(self.id, self.info_hash)

    @cached_property
    def master_trans_torrent(self):
        torrents = list(TransTorrent.objects.filter(
            what_torrent=self,
            instance__in=ReplicaSet.get_what_master().transinstance_set.all()
        ))
        if len(torrents):
            return torrents[0]
        return None

    @cached_property
    def joined_artists(self):
        return get_artists(self.info_loads['group'])

    @property
    def torrent_file_binary(self):
        return base64.b64decode(self.torrent_file)

    @cached_property
    def info_loads(self):
        return ujson.loads(self.info)

    @staticmethod
    def get_or_none(request, info_hash=None, what_id=None):
        if info_hash and what_id:
            raise Exception('Specify one.')
        if not info_hash and not what_id:
            raise Exception('Specify one.')
        try:
            if info_hash:
                return WhatTorrent.objects.get(info_hash=info_hash)
            elif what_id:
                return WhatTorrent.objects.get(id=what_id)
        except WhatTorrent.DoesNotExist:
            return None

    @staticmethod
    def is_downloaded(request, info_hash=None, what_id=None):
        w_torrent = WhatTorrent.get_or_none(request, info_hash, what_id)
        if w_torrent and w_torrent.transtorrent_set.count() > 0:
            return True
        return False

    @staticmethod
    def get_or_create(request, info_hash=None, what_id=None):
        if info_hash and what_id:
            raise Exception('Specify either an infohash OR an ID, not both.')
        if not info_hash and not what_id:
            raise Exception('You must specify an infohash or an ID.')

        try:
            if info_hash:
                if len(info_hash) != 40:
                    raise Exception('Invalid info hash.')
                return WhatTorrent.objects.get(info_hash=info_hash)
            else:
                return WhatTorrent.objects.get(id=what_id)
        except WhatTorrent.DoesNotExist:
            what = RedClient()

            if info_hash:
                data = what.request('torrent', hash=info_hash)['response']
            else:
                data = what.request('torrent', id=what_id)['response']

            r = what.get_torrent(data['torrent']['id'], full_response=True)
            filename = re.search('filename="(.*)"', r.headers['content-disposition']).group(1)
            w_torrent = WhatTorrent(
                id=int(data['torrent']['id']),
                info_hash=data['torrent']['infoHash'],
                torrent_file=base64.b64encode(r.content).decode('utf-8'),
                torrent_file_name=filename,
                retrieved=timezone.now(),
                info=ujson.dumps(data))
            w_torrent.save()
            return w_torrent


class TransTorrentBase(models.Model):
    class Meta:
        abstract = True

    sync_t_arguments = [
        'id', 'name', 'hashString', 'totalSize', 'uploadedEver', 'percentDone', 'addedDate',
        'error', 'errorString'
    ]
    sync_t_props = (
        ('torrent_id', 'id'),
        ('torrent_name', 'name'),
        ('torrent_size', 'totalSize'),
        ('torrent_uploaded', 'uploadedEver'),
        ('torrent_done', 'percentDone'),
        ('torrent_date_added', 'date_added_tz'),
        ('torrent_error', 'error'),
        ('torrent_error_string', 'errorString'),
    )

    instance = models.ForeignKey(TransInstance, on_delete=models.CASCADE)
    location = models.ForeignKey(DownloadLocation, on_delete=models.CASCADE)

    info_hash = models.CharField(max_length=40)
    torrent_id = models.IntegerField(null=True)
    torrent_name = models.TextField(null=True)
    torrent_size = models.BigIntegerField(null=True)
    torrent_uploaded = models.BigIntegerField(null=True)
    torrent_done = models.FloatField(null=True)
    torrent_date_added = models.DateTimeField(null=True)
    torrent_error = models.IntegerField(null=True)
    torrent_error_string = models.TextField(null=True)

    def sync_t_torrent(self, t_torrent=None):
        if t_torrent is None:
            t_torrent = self.instance.client.get_torrent(
                self.torrent_id, arguments=TransTorrentBase.sync_t_arguments)
            norm_t_torrent(t_torrent)

        if not match_properties(self, t_torrent, TransTorrentBase.sync_t_props):
            copy_properties(self, t_torrent, TransTorrentBase.sync_t_props)
            self.save()


class TransTorrent(TransTorrentBase):
    what_torrent = models.ForeignKey(WhatTorrent, on_delete=models.CASCADE)

    @property
    def path(self):
        return os.path.join(self.location.path, str(self.what_torrent.id))

    def sync_files(self):
        if os.path.exists(self.path):
            files = [f for f in os.listdir(self.path)]
        else:
            os.mkdir(self.path, 0o777)
            os.chmod(self.path, 0o777)
            files = []

        files_added = []
        if not any('.torrent' in f for f in files):
            files_added.append('torrent')
            torrent_path = os.path.join(self.path, self.what_torrent.torrent_file_name)
            with open(torrent_path, 'wb') as file:
                file.write(self.what_torrent.torrent_file_binary)
            os.chmod(torrent_path, 0o777)
        if not any('ReleaseInfo2.txt' == f for f in files):
            files_added.append('ReleaseInfo2.txt')
            release_info_path = os.path.join(self.path, 'ReleaseInfo2.txt')
            with open(release_info_path, 'w') as file:
                file.write(self.what_torrent.info)
            os.chmod(os.path.join(release_info_path), 0o777)
        if files_added:
            LogEntry.add(None, 'info', 'Added files {0} to {1}'
                         .format(', '.join(files_added), self))

    def __str__(self):
        return 'TransTorrent(torrent_id={0}, what_id={1}, name={2})'.format(
            self.torrent_id, self.what_torrent_id, self.torrent_name)


class LogEntry(models.Model):
    user = models.ForeignKey(User, null=True, related_name='wm_logentry', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    type = models.TextField()
    message = models.TextField()
    traceback = models.TextField(null=True)

    @staticmethod
    def add(user, log_type, message, traceback=None):
        entry = LogEntry(user=user, type=log_type, message=message, traceback=traceback)
        entry.save()


class WhatFileMetadataCache(models.Model):
    what_torrent = models.ForeignKey(WhatTorrent, on_delete=models.CASCADE)
    filename_sha256 = models.CharField(max_length=64, primary_key=True)
    filename = models.CharField(max_length=500)
    file_mtime = models.IntegerField()
    metadata_pickle = models.BinaryField()
    artists = models.CharField(max_length=200)
    album = models.CharField(max_length=200)
    title = models.CharField(max_length=200, db_index=True)
    duration = models.FloatField()

    @cached_property
    def metadata(self):
        return pickle.loads(self.metadata_pickle)

    @cached_property
    def easy(self):
        data = {
            'artist': '',
            'album': '',
            'title': '',
            'duration': self.metadata.info.length,
        }
        if self.metadata.get('albumartist') and self.metadata['albumartist'][0]:
            data['artist'] = ', '.join(self.metadata['albumartist'])
        if self.metadata.get('artist') and self.metadata['artist'][0]:
            data['artist'] = ', '.join(self.metadata['artist'])
        if self.metadata.get('performer') and self.metadata['performer'][0]:
            data['artist'] = ', '.join(self.metadata['performer'])
        if 'album' in self.metadata and self.metadata['album']:
            data['album'] = ', '.join(self.metadata['album'])
        if 'title' in self.metadata and self.metadata['title']:
            data['title'] = ', '.join(self.metadata['title'])
        return data

    def fill(self, filename, file_mtime):
        metadata = mutagen.File(filename, easy=True)
        if hasattr(metadata, 'pictures'):
            for p in metadata.pictures:
                p.data = None
        if hasattr(metadata, 'tags'):
            if hasattr(metadata.tags, '_EasyID3__id3'):
                metadata.tags._EasyID3__id3.delall('APIC')
        self.file_mtime = file_mtime
        try:
            self.metadata_pickle = pickle.dumps(metadata)
        except:
            self.metadata_pickle = pickle.dumps(metadata, pickle.HIGHEST_PROTOCOL)
            pass
        self.artists = self.easy['artist'][:200]
        self.album = self.easy['album'][:200]
        self.title = self.easy['title'][:200]
        self.duration = self.easy['duration']

    @classmethod
    def get_metadata_batch(cls, what_torrent, trans_torrent, force_update):
        torrent_path = trans_torrent.path
        cache_lines = list(what_torrent.whatfilemetadatacache_set.all())
        if len(cache_lines) and not force_update:
            for cache_line in cache_lines:
                cache_line.path = os.path.join(torrent_path, cache_line.filename)
            return sorted(cache_lines, key=lambda c: c.path)

        cache_lines = {c.filename_sha256: c for c in cache_lines}

        abs_rel_filenames = []
        for dirpath, dirnames, filenames in os.walk(torrent_path):
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() in ['.flac', '.mp3']:
                    abs_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(abs_path, torrent_path)
                    abs_rel_filenames.append((abs_path, rel_path))
        abs_rel_filenames.sort(key=lambda f: f[1])

        filename_hashes = {f[0]: hashlib.sha256(f[1].encode('utf-8')).hexdigest() for f in
                           abs_rel_filenames}
        hash_set = set(filename_hashes.values())
        old_cache_lines = []
        for cache_line in cache_lines.values():
            if cache_line.filename_sha256 not in hash_set:
                old_cache_lines.append(cache_line)
        dirty_cache_lines = []

        result = []
        for abs_path, rel_path in abs_rel_filenames:
            try:
                file_mtime = os.path.getmtime(abs_path)
                cache = cache_lines.get(filename_hashes[abs_path])
                if cache is None:
                    cache = WhatFileMetadataCache(
                        what_torrent=what_torrent,
                        filename_sha256=filename_hashes[abs_path],
                        filename=rel_path[:400],
                        file_mtime=0
                    )
                cache.path = abs_path
                if abs(file_mtime - cache.file_mtime) <= 1:
                    result.append(cache)
                    continue
                cache.fill(abs_path, file_mtime)
                dirty_cache_lines.append(cache)
                result.append(cache)
            except Exception as ex:
                print('Failed:', abs_path, ex)
        if old_cache_lines or dirty_cache_lines:
            with transaction.atomic():
                for cache_line in old_cache_lines:
                    cache_line.delete()
                for cache_line in dirty_cache_lines:
                    cache_line.save()
        return result


class LoginException(Exception):
    pass


class RequestException(Exception):
    def __init__(self, message=None, response=None):
        super(Exception, self).__init__(message)
        self.response = response


class BadIdException(RequestException):
    def __init__(self, response=None):
        super(BadIdException, self).__init__('Bad ID Parameter.', response)


class RateLimitExceededException(RequestException):
    def __init__(self, response=None):
        super(RateLimitExceededException, self).__init__('Rate limit exceeded.', response)

class WhatLoginCache(models.Model):
    cookies = models.BinaryField()
    authkey = models.TextField()
    passkey = models.TextField()

class RedClient(WhatAPI):
    def __init__(self):
        self.RED_URL = 'https://redacted.ch'
        self.RED_UPLOAD = self.RED_URL + '/upload.php'
        self.user = TrackerAccount.get_red()

        try:
            self.login_cache = WhatLoginCache.objects.get()
            super().__init__(cookies=pickle.loads(self.login_cache.cookies),
                            server=self.RED_URL)
        except:
            super().__init__(username=self.user.username,
                            password=self.user.password,
                            server=self.RED_URL)


    def _login(self):
        super()._login()
        self.login_cache, _ = WhatLoginCache.objects.get_or_create()
        self.login_cache.cookies = pickle.dumps(self.session.cookies)
        self.login_cache.authkey = self.authkey
        self.login_cache.passkey = self.passkey
        self.login_cache.save()

    def clear_login_cache(self):
        WhatLoginCache.objects.all().delete()

    def upload(self, data, files):
        payload = {}
        payload.update(data)
        payload.update({
            'submit': 'true',
            'auth': self.authkey
        })
        response = self.session.post(self.RED_UPLOAD, data=payload, files=files)
        if response.url == self.RED_UPLOAD:
            try:
                errors = self._extract_upload_errors(response.text)
            except Exception as e:
                errors = str(e)
            e = Exception('Error uploading data to Redacted. Errors: {0}'.format('; '.join(errors)))
            e.response_text = response.text
            raise e

    def _extract_upload_errors(self, html):
        pq = PyQuery(html)
        result = []
        for e in pq.find('.thin > p[style="color: red; text-align: center;"]'):
            result.append(PyQuery(e).text())
        return result