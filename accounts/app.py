from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.nav import register, Node

from accounts import views

node = Node('Accounts', 'accounts-list')
register(node, 100)


class DatacashDashboardApplication(Application):
    name = None
    list_view = views.ListView
    create_view = views.CreateView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(),
                name='accounts-list'),
            url(r'^create/$', self.create_view.as_view(),
                name='accounts-create'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = DatacashDashboardApplication()
