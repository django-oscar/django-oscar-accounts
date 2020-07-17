from django.apps import apps
from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView

from oscar_accounts.views import AccountBalanceView

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('giftcard-balance/', AccountBalanceView.as_view(), name="account-balance"),
    path('dashboard/accounts/', apps.get_app_config('accounts_dashboard').urls),
    path('', include(apps.get_app_config('oscar').urls[0])),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path('404', TemplateView.as_view(template_name='404.html')),
        path('500', TemplateView.as_view(template_name='500.html'))
    ]
