from django.contrib import admin
from home.models import DownloadLocation, ReplicaSet, TransInstance

admin.site.register(DownloadLocation)
admin.site.register(ReplicaSet)
admin.site.register(TransInstance)