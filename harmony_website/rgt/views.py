from django.shortcuts import render
from rgt.models import RgtCheck, RgtEvent, RgtTest, RgtTestEvent
from rgt.filters import TestFilter
from django.views import generic

# Create your views here.


def index(request):
    """
    View function for the home page of the site.

    :param request: Request from user for index.
    :return: Rendered html.
    """

    # Generate counts of the various objects.
    num_tests = RgtTest.objects.all().count()
    num_test_events = RgtTestEvent.objects.all().count()

    # Tests by ACME
    num_ACME_tests = RgtTest.objects.filter(application__exact='ACME').count()
    num_event_types = RgtEvent.objects.count()

    num_applications = RgtTest.objects.values_list('application').distinct().count()

    context = {
        'num_tests': num_tests,
        'num_test_events': num_test_events,
        'num_ACME_tests': num_ACME_tests,
        'num_event_types': num_event_types,
        'num_applications': num_applications,
    }

    return render(request, 'index.html', context=context)


def test_search(request):
    test_list = RgtTest.objects.all()
    test_filter = TestFilter(request.GET, queryset=test_list)
    return render(request, 'rgt/test_list.html', {'filter': test_filter})


class TestListView(generic.ListView):
    model = RgtTest
    context_object_name = 'test_list'
    template_name = 'rgt/test_list.html'


class TestDetailView(generic.DetailView):
    model = RgtTest
    context_object_name = 'test'
    template_name = 'rgt/test_detail.html'

    def get_object(self):
        return self.model.objects.filter(application__exact=self.kwargs['app'],
                                         testname__exact=self.kwargs['testname'],
                                         harness_uid__exact=self.kwargs['hid']).first()


class AppTestListView(generic.ListView):
    model = RgtTest
    context_object_name = 'app_test_list'
    template_name = 'rgt/app_test_list.html'

    def get_queryset(self):
        return self.model.objects.filter(application__exact=self.kwargs['app'])


class TestnameTestListView(generic.ListView):
    model = RgtTest
    context_object_name = 'testname_test_list'
    template_name = 'rgt/testname_test_list.html'

    def get_queryset(self):
        return self.model.objects.filter(application__exact=self.kwargs['app'],
                                         testname__exact=self.kwargs['testname'])
