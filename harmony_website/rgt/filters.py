from rgt.models import RgtTest
import django_filters
from django.db.models import Count
from django import forms


class TestFilter(django_filters.FilterSet):
    APP_CHOICES_LIST = RgtTest.objects.order_by().values_list('application').distinct().order_by('application')
    APP_CHOICES = [(i[0], i[0]) for i in APP_CHOICES_LIST]
    application = django_filters.MultipleChoiceFilter(
        choices=APP_CHOICES,
        label='Applications',
    )

    class Meta:
        model = RgtTest
        fields = ['application']
