import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from WhatManager2.settings import MEDIA_ROOT
from home.models import ReplicaSet, TrackerAccount, DownloadLocation

def create_superuser():
    if User.objects.count() < 1:
        print('There are no user accounts. I will create a superuser for you.')
        u = User.objects.create_superuser(
            username=os.getenv('WM_USER'),
            password=os.getenv('WM_PASSWORD'),
        )

def ensure_replica_set_exists():
    for zone in TrackerAccount.ZONES:
        try:
            ReplicaSet.objects.get(zone=zone[0])
        except ReplicaSet.DoesNotExist:
            print('There is no replica set with the name {0}. I will create one.'.format(zone[0]))
            replica_set = ReplicaSet(
                zone = zone[0],
                name = 'master',
            )
            replica_set.save()

def configure_download_locations():
    ZONES = []
    for zone in TrackerAccount.ZONES:
        ZONES.append(zone[0])

    for dl in DownloadLocation.objects.all():
        if dl.zone in ZONES:
            ZONES.remove(dl.zone)

    for zone in ZONES:
        print('There is no download location for zone {0}. I will use the default path.'.format(zone))
        dl = DownloadLocation(
            path = os.path.join(MEDIA_ROOT, '/downloads/', zone)
        )
        dl.save()

def add_trans_instance(
    host, 
    port, 
    username=os.getenv('WM_USER', 'transmission'), 
    password=os.getenv('TRANSMISSION_PASSWORD')):
    pass


class Command(BaseCommand):
    help = 'Configures WM for user within a docker container'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        create_superuser()
        ensure_replica_set_exists()
