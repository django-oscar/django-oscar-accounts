from django.conf.urls import patterns, include
from django.contrib import admin

from oscar.app import application

from oscar_accounts.dashboard.app import application as accounts_app
from oscar_accounts.api.app import application as api_app

admin.autodiscover()

urlpatterns = patterns('',
    (r'^dashboard/accounts/', include(accounts_app.urls)),
    (r'^api/', include(api_app.urls)),
    (r'', include(application.urls)),
)
