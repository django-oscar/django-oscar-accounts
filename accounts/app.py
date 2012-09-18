from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import Application
from oscar.apps.dashboard.nav import register, Node

from accounts import views

node = Node(_('Accounts'))
node.add_child(Node(_('Code accounts'), 'accounts-list'))
node.add_child(Node(_('Transfers'), 'transfers-list'))
register(node, 100)


class DatacashDashboardApplication(Application):
    name = None
    list_view = views.ListView
    create_view = views.CreateView
    detail_view = views.DetailView
    transfer_list_view = views.TransferListView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(),
                name='accounts-list'),
            url(r'^create/$', self.create_view.as_view(),
                name='accounts-create'),
            url(r'^(?P<pk>\d+)/$', self.detail_view.as_view(),
                name='accounts-detail'),
            url(r'^transfers/$', self.transfer_list_view.as_view(),
                name='transfers-list'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = DatacashDashboardApplication()
