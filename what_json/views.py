import os
from random import choice
import shutil
import socket
import traceback
import time

from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import WhatManager2.checks
from WhatManager2 import manage_torrent, trans_sync
from WhatManager2.settings import MIN_FREE_DISK_SPACE
from WhatManager2.templatetags.custom_filters import filesizeformat
from WhatManager2.utils import json_return_method
from home.models import DownloadLocation, LogEntry, RedClient, ReplicaSet, TorrentAlreadyAddedException, TrackerAccount, TransInstance, TransTorrent, WhatTorrent
from what_json import utils


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def sync(request):
    start_time = time.time()
    part_start_time = time.time()
    try:
        trans_sync.sync_profile(request)
        profile_time = time.time() - part_start_time
        part_start_time = time.time()
    except Exception as ex:
        profile_time = 0
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error', 'Error syncing profile: {0}'.format(ex), tb)

    try:
        master = ReplicaSet.get_what_master()
        trans_sync.sync_all_instances_db(request, master)
        master_db_time = time.time() - part_start_time
        part_start_time = time.time()
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error', 'Error syncing master DB: {0}({1})'.format(
            type(ex).__name__, ex), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb
        }

    # try:
    # if trans_sync.sync_fulltext():
    # LogEntry.add(request.user, u'error', u'Fulltext table was out of sync. Synced.')
    # except Exception as ex:
    # tb = traceback.format_exc()
    # LogEntry.add(request.user, u'error', u'Error syncing fulltext table: {0}'.format(ex), tb)
    # return {
    # 'success': False,
    # 'error': unicode(ex),
    # 'traceback': tb
    # }

    time_taken = time.time() - start_time
    LogEntry.add(request.user, 'info',
                 'Completed what.cd sync in {0:.3f}s. Profile in {1:.3f}s. Master DB in {2:.3f}s.'
                 .format(time_taken, profile_time, master_db_time))
    return {
        'success': True
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def sync_replicas(request):
    start_time = time.time()
    part_start_time = time.time()

    master = ReplicaSet.get_what_master()
    try:
        for replica_set in ReplicaSet.objects.all():
            if replica_set.id != master.id:
                trans_sync.sync_all_instances_db(request, replica_set)
        replicas_dbs_time = time.time() - part_start_time
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error', 'Error syncing replicas DB: {0}'.format(ex), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb
        }

    try:
        trans_sync.sync_all_replicas_to_master()
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error', 'Error running replica sync: {0}'.format(ex), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb
        }
    time_taken = time.time() - start_time

    LogEntry.add(request.user, 'info',
                 'Completed replica sync in {0:.3f}s. DB in {1:.3f}s.'.format(time_taken,
                                                                               replicas_dbs_time))
    return {
        'success': True
    }


@login_required
@permission_required('home.run_checks', raise_exception=True)
@json_return_method
def checks(request):
    try:
        result = WhatManager2.checks.run_checks()
    except Exception as ex:
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error', 'Error running checks: {0}'.format(ex), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb
        }
    result.update({
        'success': True
    })
    return result


@login_required
@require_POST
@json_return_method
@csrf_exempt
def add_torrent(request):
    if not request.user.has_perm('home.add_whattorrent'):
        return {
            'success': False,
            'error': 'You don\'t have permission to add torrents. Talk to the administrator.',
        }

    try:
        if 'dir' in request.POST:
            download_location = DownloadLocation.objects.get(
                zone=TrackerAccount.ZONE_RED,
                path=request.POST['dir']
            )
        else:
            download_location = TrackerAccount.get_red().download_location
    except DownloadLocation.DoesNotExist:
        return {
            'success': False,
            'error': 'Download location does not exist.',
        }

    if download_location.free_space_percent < MIN_FREE_DISK_SPACE:
        LogEntry.add(request.user, 'error', 'Failed to add torrent. Not enough disk space.')
        return {
            'success': False,
            'error': 'Not enough free space on disk.',
        }

    try:
        what_id = int(request.POST['id'])
    except (ValueError, MultiValueDictKeyError):
        return {
            'success': False,
            'error': 'Invalid id',
        }

    instance = ReplicaSet.get_what_master().get_preferred_instance()

    try:
        if WhatTorrent.is_downloaded(request, what_id=what_id):
            m_torrent = TransTorrent.objects.filter(what_torrent_id=what_id)[0]
            raise TorrentAlreadyAddedException()
        m_torrent = manage_torrent.add_torrent(request, instance, download_location, what_id, True)
        m_torrent.what_torrent.added_by = request.user
        m_torrent.what_torrent.save()
    except TorrentAlreadyAddedException:
        LogEntry.add(request.user, 'info',
                     'Tried adding what_id={0}, already added.'.format(what_id))
        what_torrent = WhatTorrent.get_or_none(request, what_id=what_id)
        result = {
            'success': False,
            'error_code': 'already_added',
            'error': 'Already added.',
            'torrent_id': m_torrent.what_torrent_id,
        }
        if m_torrent.what_torrent.info_category_id == 1:
            result['artist'] = (what_torrent.info_artist if what_torrent
                                else '<<< Unable to find torrent >>>')
            result['title'] = (what_torrent.info_title if what_torrent
                               else '<<< Unable to find torrent >>>')
        return result
    except Exception as ex:
        raise ex
        tb = traceback.format_exc()
        LogEntry.add(request.user, 'error',
                     'Tried adding what_id={0}. Error: {1}'.format(what_id, str(ex)), tb)
        return {
            'success': False,
            'error': str(ex),
            'traceback': tb,
        }

    tags = request.POST.get('tags')
    if tags:
        m_torrent.what_torrent.tags = tags
        m_torrent.what_torrent.save()

    LogEntry.add(request.user, 'action', 'Added {0} to {1}'.format(m_torrent, m_torrent.instance))

    result = {
        'success': True,
    }
    if m_torrent.what_torrent.info_category_id == 1:
        result['artist'] = m_torrent.what_torrent.info_artist,
        result['title'] = m_torrent.what_torrent.info_title,
    return result


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def run_load_balance(request):
    torrent_count = int(request.GET['count'])
    source_instance = request.GET['source']

    instance = TransInstance.objects.get(name=source_instance)
    for i in range(torrent_count):
        t = choice(instance.transtorrent_set.filter(torrent_uploaded=0))
        t = manage_torrent.move_torrent(t, ReplicaSet.get_what_master().get_preferred_instance())

    return {
        'success': True
    }


@login_required
@user_passes_test(lambda u: u.is_superuser is True)
@json_return_method
def move_torrent_to_location(request):
    what_id = int(request.GET['id'])
    new_location = DownloadLocation.objects.get(zone=TrackerAccount.ZONE_RED, path=request.GET['path'])
    what_torrent = WhatTorrent.objects.get(id=what_id)
    trans_torrent = TransTorrent.objects.get(
        instance__in=ReplicaSet.get_what_master().transinstance_set.all(),
        what_torrent=what_torrent)

    if trans_torrent.location.id == new_location.id:
        raise Exception('Torrent is already there.')

    print('Source is', trans_torrent.location.path)
    print('Destination is', new_location.path)
    print('Instance is', trans_torrent.instance.name)
    print('Size is', trans_torrent.torrent_size)
    print('Name is', trans_torrent.torrent_name)

    client = trans_torrent.instance.client
    client.stop_torrent(trans_torrent.torrent_id)
    source_path = os.path.join(trans_torrent.location.path, str(what_torrent.id))
    shutil.move(source_path, new_location.path)
    client.move_torrent_data(trans_torrent.torrent_id,
                             os.path.join(new_location.path, str(what_torrent.id)))
    trans_torrent.location = new_location
    trans_torrent.save()
    client.verify_torrent(trans_torrent.torrent_id)
    client.start_torrent(trans_torrent.torrent_id)
    return {
        'success': True
    }


@login_required
@json_return_method
@csrf_exempt
@permission_required('home.view_whattorrent', raise_exception=True)
def torrents_info(request):
    def get_response(id, torrent):
        response = {'id': id}
        if torrent is None:
            response['status'] = 'missing'
        elif torrent.torrent_done == 1:
            response['status'] = 'downloaded'
        else:
            response['status'] = 'downloading'
            response['progress'] = torrent.torrent_done
        return response

    ids = [int(i) for i in request.POST['ids'].split(',')]
    torrents = TransTorrent.objects.filter(what_torrent_id__in=ids)
    torrents = {t.what_torrent_id: t for t in torrents}
    for torrent in torrents.values():
        if torrent.torrent_done < 1:
            torrent.sync_t_torrent()

    return [get_response(id, torrents.get(id)) for id in ids]


@login_required
@json_return_method
@user_passes_test(lambda u: u.is_superuser is True)
def what_proxy(request):
    get = dict(request.GET.lists())
    action = get['action']
    del get['action']
    if 'auth' in get:
        del get['auth']
    what = RedClient()
    response = what.request(action, **get)
    return response


@login_required
@json_return_method
@user_passes_test(lambda u: u.is_superuser is True)
def refresh_whattorrent(request):
    what_torrent = None
    if 'id' in request.GET:
        what_torrent = WhatTorrent.objects.get(id=request.GET['id'])
    what_client = RedClient()
    return utils.refresh_whattorrent(what_client, what_torrent)
