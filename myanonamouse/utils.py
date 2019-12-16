import re
import requests
import pickle
import time

from myanonamouse.models import MAMLoginCache
from home.models import TrackerAccount


class MAMException(Exception):
    pass


class LoginException(MAMException):
    pass


class MAMClient(object):
    def __init__(self, username, password):
        self.MAM_URL = 'https://www.myanonamouse.net'
        self.MAM_LOGIN = self.MAM_URL + '/takelogin.php'
        self.MAM_GET_TORRENT = self.MAM_URL + '/t/{0}'

        self.username = username
        self.password = password
        self.session = requests.Session()
        try:
            login_cache = MAMLoginCache.objects.get()
            for cookie in pickle.loads(login_cache.cookies):
                self.session.cookies.set_cookie(cookie)
        except MAMLoginCache.DoesNotExist:
            pass

    def _login(self):
        data = {
            'username': self.username,
            'password': self.password,
        }
        r = self.session.post(self.MAM_LOGIN, data=data, allow_redirects=False)
        if r.status_code != 302:
            raise LoginException()
        if r.headers['location'] != '/index.php':
            raise LoginException()
        MAMLoginCache.objects.all().delete()
        login_cache = MAMLoginCache(cookies=pickle.dumps([c for c in self.session.cookies]))
        login_cache.save()

    def request(self, url, try_login=True):
        resp = self.session.request('GET', url, allow_redirects=False)
        if resp.status_code == 302:
            if resp.headers['location'].startswith('/login.php?'):
                if try_login:
                    self._login()
                    return self._request(url, try_login=False)
                else:
                    raise LoginException()
            else:
                raise MAMException('Request redirect: {0}'.format(resp.headers['location']))
        elif resp.status_code != 200:
            raise MAMException()
        return resp

    def download_torrent(self, torrent_url):
        for i in range(3):
            try:
                r = self.request(torrent_url)
                if 'application/x-bittorrent' in r.headers['content-type']:
                    filename = re.search('filename="(.*)"',
                                         r.headers['content-disposition']).group(1)
                    return filename, r.content
                else:
                    raise Exception('Wrong status_code or content-type')
            except Exception as ex:
                print('Error while download MAM torrent. Will retry: {0}'.format(ex))
                time.sleep(3)
                download_exception = ex
        raise download_exception

    def get_torrent(self, torrent_id):
        return self.request(self.MAM_GET_TORRENT.format(torrent_id))

    @staticmethod
    def get():
        user = TrackerAccount.get_mam()
        return MAMClient(user.username, user.password)
