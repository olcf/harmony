from django.urls import path, re_path
from rgt import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tests/', views.TestListView.as_view(), name='tests'),
    # Only match harness uids that consist of numbers
    # TODO: Think about changing this from harness uid to application/testname/testinstance.
    # TODO: Not sure if necessary though.
    re_path(r'^tests/(?P<app>[-.\w]+)$',
            views.AppTestListView.as_view(), name='app-test-list'),
    re_path(r'^tests/(?P<app>[-.\w]+)/(?P<testname>[-.\w]+)$',
            views.TestnameTestListView.as_view(), name='testname-test-list'),
    re_path(r'^tests/(?P<app>[-.\w]+)/(?P<testname>[-.\w]+)/(?P<hid>[.\d]+)$',
            views.TestDetailView.as_view(), name='test-detail'),
]
