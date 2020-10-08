from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Course
from .forms import ModuleFormSet


# use Mixins to add additional functions for classes using views

# we can use this class in every view when any object has an "owner" attribute
class OwnerMixin(object):
    # get all objects for current user
    def get_queryset(self):
        qs = super(OwnerMixin, self).get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin(object):
    # used for forms view or vies based on classes
    # save a copy for ModelForm, and redirect user to success url
    # we override this method to set current user as author of saved object
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(OwnerEditMixin, self).form_valid(form)


# this inherit from OwnerMixin
class OwnerCourseMixin(OwnerMixin,
                       LoginRequiredMixin):
    model = Course
    fields = ['subject', 'title', 'slug', 'overview']
    # manage_course_list is connected with ManageCourseListView (?)
    success_url = reverse_lazy('manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin,
                           OwnerEditMixin):
    # fields used to create form view
    fields = ['subject', 'title', 'slug', 'overview']
    # manage_course_list is connected with ManageCourseListView (?)
    success_url = reverse_lazy('manage_course_list')
    template_name = 'courses/manage/course/form.html'


# classes bellow use OwnerCourseMixin as template for views

# list courses
class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'


# create new course object
class CourseCreateView(PermissionRequiredMixin,
                       OwnerCourseEditMixin,
                       CreateView):
    permission_required = 'courses.add_course'


# we can edit course
class CourseUpdateView(PermissionRequiredMixin,
                       OwnerCourseEditMixin,
                       UpdateView):
    permission_required = 'courses.change_course'


# delete course
class CourseDeleteView(PermissionRequiredMixin,
                       OwnerCourseMixin,
                       DeleteView):
    template_name = 'courses/manage/course/delete.html'
    # manage_course_list is connected with ManageCourseListView (?)
    success_url = reverse_lazy('manage_course_list')
    permission_required = 'courses.delete_course'


# this view handles the collection of forms for added, update or delete modules for current course
# TemplateResponseMixin generate forms and send back HTTP request
class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    # create set of forms
    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)

    # get HTTP request and handle the type of request (depends it is GET or POST)
    def dispatch(self, request, pk):
        self.course = get_object_or_404(Course,
                                        id=pk,
                                        owner=request.user)
        return super(CourseModuleUpdateView, self).dispatch(request, pk)

    # for GET request, we build empty element ModuleFormSet and generate in form with current Course object
    # by method render_to_response from TemplateResponseMixin
    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({'course': self.course,
                                        'formset': formset})

    # for POST request, at first is built ModuleFormSet element, later the method is_valid() is executed
    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({'course': self.course,
                                        'formset': formset})
