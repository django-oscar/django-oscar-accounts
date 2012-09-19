from django.conf.urls import patterns, include
from django.contrib import admin

from oscar.app import shop

from accounts.dashboard.app import application as accounts_app

admin.autodiscover()

urlpatterns = patterns('',
    (r'^dashboard/accounts/', include(accounts_app.urls)),
    (r'', include(shop.urls)),
)
