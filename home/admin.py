from django.contrib import admin
from home.models import DownloadLocation, ReplicaSet, TransInstance, TrackerAccount, ResourceAccount

admin.site.register(DownloadLocation)
admin.site.register(ReplicaSet)
admin.site.register(TransInstance)
admin.site.register(TrackerAccount)
admin.site.register(ResourceAccount)