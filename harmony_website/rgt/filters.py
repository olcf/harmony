from rgt.models import RgtTest, RgtFailure
import django_filters
from django.db.models import Q


APP_CHOICES_LIST = RgtTest.objects.order_by().values_list('application').distinct().order_by('application')
APP_CHOICES = [('all', 'All')] + [(i[0], i[0]) for i in APP_CHOICES_LIST]

STATUS_CHOICES = [('success', 'Success'), ('failure', 'Failure')]

FAILURE_CHOICES_LIST = RgtFailure.objects.order_by().values_list('failure_label').order_by('failure_label')
FAILURE_CHOICES = [(i[0], i[0]) for i in FAILURE_CHOICES_LIST]
FAILURE_CHOICES = [('any', 'Any Failure'), ('none', 'None')] + FAILURE_CHOICES


def filter_by_status(queryset, name, value):
    if value == 'success':
        return queryset.filter(Q(build_status=0), Q(submit_status=0), Q(check_status=0))
    elif value == 'failure':
        return queryset.filter(~Q(build_status=0) | ~Q(submit_status=0) | ~Q(check_status=0))
    else:
        return queryset


def filter_by_failure(queryset, name, value):
    if 'any' in value:
        return queryset.exclude(rgttestfailure__isnull=True)
    elif 'none' in value:
        return queryset.filter(rgttestfailure__isnull=True)
    else:
        if type(value) == str:
            return queryset.filter(rgttestfailure__failure_id__failure_label=value)
        else:
            return queryset.filter(rgttestfailure__failure_id__failure_label__in=value)


def filter_by_application(queryset, name, value):
    if 'all' in value:
        return queryset
    else:
        return queryset.filter(application__in=value)


class BaseFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=STATUS_CHOICES,
        label='Status',
        field_name='status',
        method=filter_by_status,

    )

    failure = django_filters.MultipleChoiceFilter(
        choices=FAILURE_CHOICES,
        label='Failure Type',
        field_name='failure',
        method=filter_by_failure,
    )

    class Meta:
        model = RgtTest
        fields = ['status', 'failure']


class TestFilter(BaseFilter):
    application = django_filters.MultipleChoiceFilter(
        choices=APP_CHOICES,
        label='Applications',
        method=filter_by_application,
    )

    class Meta:
        model = RgtTest
        fields = ['application']
