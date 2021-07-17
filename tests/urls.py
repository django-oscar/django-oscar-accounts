from django.apps import apps
from django.contrib import admin
from django.urls import include, path

admin.autodiscover()

urlpatterns = [
    path('dashboard/accounts/', apps.get_app_config('accounts_dashboard').urls),
    path('api/', apps.get_app_config('oscar_accounts_api').urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include(apps.get_app_config('oscar').urls[0])),
]
