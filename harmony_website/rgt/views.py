from django.shortcuts import render
from rgt.models import RgtCheck, RgtEvent, RgtTest, RgtTestEvent, RgtTestFailure
from rgt.forms import TestFailureForm
from rgt.filters import TestFilter, BaseFilter
from django.views import generic
from bootstrap_modal_forms.mixins import PassRequestMixin, DeleteAjaxMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.template.base import VariableDoesNotExist

# Create your views here.


class AjaxableResponseMixin:
    """
    Mixin to add AJAX support to a form.
    """
    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk
            }
            return JsonResponse(data)
        else:
            return response


def index(request):
    """
    View function for the home page of the site.

    :param request: Request from user for index.
    :return: Rendered html.
    """

    # Generate counts of the various objects.
    num_tests = RgtTest.objects.all().count()
    num_test_events = RgtTestEvent.objects.all().count()

    num_event_types = RgtEvent.objects.count()

    num_applications = RgtTest.objects.values_list('application').distinct().count()

    context = {
        'num_tests': num_tests,
        'num_test_events': num_test_events,
        'num_event_types': num_event_types,
        'num_applications': num_applications,
    }

    return render(request, 'index.html', context=context)


class CustomListView(generic.ListView):
    filter_class = BaseFilter
    context_filter_name = 'filter'

    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super(CustomListView, self).get_context_data(**kwargs)
        context['test_failure_list'] = RgtTestFailure.objects.all()
        context[self.context_filter_name] = self.filter_class(self.request.GET, queryset=self.get_queryset())
        return context

    def restrict_queryset(self):
        return self.model.objects.all()

    def get_queryset(self):
        filtered_qs = self.filter_class(
            self.request.GET,
            queryset=self.restrict_queryset()
        ).qs
        return filtered_qs


class TestListView(CustomListView):
    model = RgtTest
    context_object_name = 'test_list'
    filter_class = TestFilter
    template_name = 'rgt/test_list.html'


class TestDetailView(generic.DetailView):
    model = RgtTest
    context_object_name = 'test'
    template_name = 'rgt/test_detail.html'

    def get_object(self):
        return self.model.objects.filter(application__exact=self.kwargs['app'],
                                         testname__exact=self.kwargs['testname'],
                                         harness_uid__exact=self.kwargs['hid']).first()


class AppTestListView(CustomListView):
    model = RgtTest
    context_object_name = 'app_test_list'
    template_name = 'rgt/app_test_list.html'

    def restrict_queryset(self):
        return self.model.objects.filter(application__exact=self.kwargs['app'])


class TestnameTestListView(CustomListView):
    model = RgtTest
    context_object_name = 'testname_test_list'
    template_name = 'rgt/testname_test_list.html'

    def restrict_queryset(self):
        return self.model.objects.filter(application__exact=self.kwargs['app'],
                                         testname__exact=self.kwargs['testname'])


class FailureCreateView(PassRequestMixin, SuccessMessageMixin, generic.CreateView, AjaxableResponseMixin):
    form_class = TestFailureForm
    template_name = 'rgt/failure_create_form.html'
    success_message = 'Success: Failure was created.'

    def __init__(self):
        super(FailureCreateView, self).__init__()
        self._test = None

    @property
    def test(self):
        """
        Do a lazy evaluation on the test this view is for. This makes it so that the path can be used.

        :return: The test object from the table.
        """
        if not self._test:
            self._test = RgtTest.objects.filter(application__exact=self.kwargs['app'],
                                                testname__exact=self.kwargs['testname'],
                                                harness_uid__exact=self.kwargs['hid']).first()
        return self._test

    def get_context_data(self, **kwargs):
        context = super(FailureCreateView, self).get_context_data(**kwargs)
        context['test'] = self.test
        return context

    def post(self, request, *args, **kwargs):
        form = TestFailureForm(request.POST, request=request)
        if form.is_valid():
            form.save(test=self.test)
            return HttpResponseRedirect(
                get_next_url(self.request,
                             reverse_lazy('test-detail', kwargs={'app': self.kwargs['app'],
                                                                 'testname': self.kwargs['testname'],
                                                                 'hid': self.kwargs['hid']}))
                )
        else:
            return JsonResponse({'success': 0})


class FailureDeleteView(DeleteAjaxMixin, generic.DeleteView):
    model = RgtTestFailure
    template_name = 'rgt/failure_delete_form.html'
    success_message = 'Success: Failure was deleted.'

    def __init__(self):
        super(FailureDeleteView, self).__init__()
        self._failure = None

    @property
    def failure(self):
        """
        Do a lazy evaluation on the failure this test is for. This lets us use the path.

        :return: The failure object connected to this test.
        """
        if not self._failure:
            self._failure = RgtTestFailure.objects.filter(test_id__application__exact=self.kwargs['app'],
                                                          test_id__testname__exact=self.kwargs['testname'],
                                                          test_id__harness_uid__exact=self.kwargs['hid']).first()

        return self._failure

    def get_object(self, queryset=None):
        return self.failure

    def get_context_data(self, **kwargs):
        context = super(FailureDeleteView, self).get_context_data(**kwargs)
        context['failure'] = self.failure
        return context

    def get_success_url(self):
        return get_next_url(self.request,
                            reverse_lazy('test-detail', kwargs={'app': self.kwargs['app'],
                                         'testname': self.kwargs['testname'],
                                         'hid': self.kwargs['hid']}))


def get_next_url(request, default_next):
    try:
        return request.POST.get('next')
    except VariableDoesNotExist:
        return default_next
