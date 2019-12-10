from django.conf.urls import url
from .views import (add_torrent, checks, move_torrent_to_location,
                             refresh_whattorrent, run_load_balance, sync,
                             sync_replicas, torrents_info, what_proxy)

app_name = 'what_json'

urlpatterns = [
    url(r'^checks$', checks, name='checks'),
    url(r'^add_torrent$', add_torrent, name='add_torrent'),
    url(r'^sync$', sync, name='sync'),
    url(r'^sync_replicas$', sync_replicas, name='sync_replicas'),
    url(r'^load_balance$', run_load_balance, name='run_load_balance'),
    url(r'^move_torrent$', move_torrent_to_location, name='move_torrent_to_location'),
    url(r'^torrents_info$', torrents_info, name='torrents_info'),
    url(r'^refresh_whattorrent$', refresh_whattorrent, name='refresh_whattorrent'),
    url(r'^what_proxy$', what_proxy, name='what_proxy'),
]
