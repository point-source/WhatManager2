# Generated by Django 2.1.4 on 2018-12-09 22:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_auto_20161206_1624'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='whattorrent',
            options={'permissions': (('download_whattorrent', 'Can download and play torrents.'),)},
        ),
    ]
