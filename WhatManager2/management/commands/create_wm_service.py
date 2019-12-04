import os

from django.core.management.base import BaseCommand

from WhatManager2.utils import write_text

wm2_service_template = '''[Unit]
Description=WhatManager2 gunicorn daemon
After=network.target

[Service]
Type=notify
RuntimeDirectory=gunicorn
WorkingDirectory=<<<wm2_dir>>>
ExecStart=<<<wm2_dir>>>/.venv/bin/gunicorn WhatManager2.wsgi:application --bind 0.0.0.0:80
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target'''.replace('<<<wm2_dir>>>', os.getcwd())

class Command(BaseCommand):
    help = 'Creates WM systemd service to start gunicorn server at boot'

    def handle(self, *args, **options):
        write_text('/lib/systemd/system/whatmanager.service', wm2_service_template)