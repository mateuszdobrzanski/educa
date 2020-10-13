from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Course
from .forms import ModuleFormSet
from django.forms.models import modelform_factory
from django.apps import apps
from .models import Module, Content


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
    # manage_course_list is connected with courses.url
    success_url = reverse_lazy('manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin,
                           OwnerEditMixin):
    # fields used to create form view
    fields = ['subject', 'title', 'slug', 'overview']
    # manage_course_list is connected with courses.url
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
    # manage_course_list is connected with courses.url
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


# class can handle create/update form for any type of content
# one form for multiple types
class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'

    # check if model is from available list, next, using django.apps we get properly class name
    def get_model(self, model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses',
                                  model_name=model_name)
        return None

    # here, we dynamically build a form using modelform_factory()
    # using exclude, we excluding fields what we don't contain in form, another one will be added automatically
    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(model, exclude=['owner',
                                                 'order',
                                                 'created',
                                                 'updated'])
        return Form(*args, **kwargs)

    # gets URL parameters and contain as class attributes
    # id None means create new object object
    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(Module,
                                       id=module_id,
                                       course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model,
                                         id=id,
                                         owner=request.user)
        return super().dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form,
                                        'object': self.obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model,
                             instance=self.obj,
                             data=request.POST,
                             files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # new content
                Content.objects.create(module=self.module,
                                       item=obj)
            return redirect('module_content_list', self.module.id)

        return self.render_to_response({'form': form,
                                        'object': self.obj})


# with this class we can easily delete content from module
class ContentDeleteView(View):

    def post(self, request, id):
        content = get_object_or_404(Content,
                                    id=id,
                                    module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)
