from django.conf.urls import include, url
from django.contrib import admin
from oscar.app import application

from oscar_accounts.api.app import application as api_app
from oscar_accounts.dashboard.app import application as accounts_app

admin.autodiscover()

urlpatterns = [
    url(r'^dashboard/accounts/', accounts_app.urls),
    url(r'^api/', api_app.urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'', application.urls),
]
