from django.apps import apps
from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^dashboard/accounts/', apps.get_app_config('accounts_dashboard').urls),
    url(r'^api/', apps.get_app_config('oscar_accounts_api').urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^', include(apps.get_app_config('oscar').urls[0])),
]
