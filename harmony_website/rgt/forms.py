from django import forms
from rgt.models import RgtTest, RgtTestFailure
from django.db.models import Count
from bootstrap_modal_forms.mixins import PopRequestMixin, CreateUpdateAjaxMixin


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


class TestFailureForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    class Meta:
        model = RgtTestFailure
        fields = ['failure_id', 'failure_details']

    def save(self, test=None, commit=True):
        test_failure = super(TestFailureForm, self).save(commit=False)
        test_failure.test_id = test
        if commit:
            test_failure.save()
        return test_failure
