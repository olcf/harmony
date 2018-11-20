from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from rgt.models import RgtTest
from django.db.models import Count


class ApplicationSelectForm(forms.Form):
    distinct = RgtTest.objects.values(
        'application'
    ).annotate(
        app_count=Count('application')
    ).filter(app_count=1)
    APP_CHOICES = RgtTest.objects.filter(application__in=[item['application'] for item in distinct])

    application_choices = forms.MultipleChoiceField(
        label="Select multiple.",
        help_text="Applications to search through. (default: all)",
        widget=forms.widgets.CheckboxSelectMultiple,
        choices=APP_CHOICES,
        initial=[c for c in APP_CHOICES]
    )
