from django.urls import path, re_path
from rgt import views
from django_filters.views import FilterView
from rgt import filters

urlpatterns = [
    path('', views.index, name='index'),
    # path('tests/', views.TestListView.as_view(), name='test-list'),
    path('tests/', FilterView.as_view(filterset_class=filters.TestFilter,
                                      template_name='rgt/test_list.html'), name='test-list'),
    # Only match harness uids that consist of numbers
    # TODO: Think about changing this from harness uid to application/testname/testinstance.
    # TODO: Not sure if necessary though.
    re_path(r'^tests/(?P<app>[-.\w]+)$',
            views.AppTestListView.as_view(), name='app-test-list'),
    re_path(r'^tests/(?P<app>[-.\w]+)/(?P<testname>[-.\w]+)/$',
            views.TestnameTestListView.as_view(), name='testname-test-list'),
    re_path(r'^tests/(?P<app>[-.\w]+)/(?P<testname>[-.\w]+)/(?P<hid>[.\d]+)/$',
            views.TestDetailView.as_view(), name='test-detail'),
    # Allow any characters at the end because we need to pass what the next url is after each form is submitted.
    re_path(r'^tests/(?P<app>[-.\w]+)/(?P<testname>[-.\w]+)/(?P<hid>[.\d]+)/create/*$',
            views.FailureCreateView.as_view(), name='failure-create'),
    re_path(r'^tests/(?P<app>[-.\w]+)/(?P<testname>[-.\w]+)/(?P<hid>[.\d]+)/delete/*$',
            views.FailureDeleteView.as_view(), name='failure-delete'),
]
