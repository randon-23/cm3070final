from django.contrib import admin
from .models import *
# class AccountAdmin(admin.ModelAdmin): to override the default admin view

admin.site.register(Account)
admin.site.register(Notification)