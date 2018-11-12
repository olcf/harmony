from django.shortcuts import render
from rgt.models import RgtCheck, RgtEvent, RgtTest, RgtTestEvent
from django.db.models import Count

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

    context = {
        'num_tests': num_tests,
        'num_test_events': num_test_events,
        'num_ACME_tests': num_ACME_tests,
        'num_event_types': num_event_types,
    }

    return render(request, 'index.html', context=context)
