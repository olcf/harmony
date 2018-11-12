from django.contrib import admin
from rgt.models import RgtCheck, RgtEvent, RgtTest, RgtTestEvent

# Register your models here.


@admin.register(RgtCheck)
class RgtCheckAdmin(admin.ModelAdmin):
    list_display = ('check_uid', 'check_desc')


@admin.register(RgtEvent)
class RgtEventAdmin(admin.ModelAdmin):
    list_display = ('event_uid', 'event_name')


@admin.register(RgtTest)
class RgtTestAdmin(admin.ModelAdmin):
    list_filter = ('check_status',)
    list_display = ('application', 'testname', 'harness_uid')


@admin.register(RgtTestEvent)
class RgtTestEventAdmin(admin.ModelAdmin):
    list_display = ('test_id', 'event_id')
