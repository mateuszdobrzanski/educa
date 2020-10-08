from django.shortcuts import render
from django.views.generic.list import ListView
from .models import Course


# this inherit LisView view
class MangeCoursesListView(ListView):
    model = Course
    template_name = 'courses/manage/course/list.html'

    # override default queryset to get all courses for current user
    def get_queryset(self):
        qs = super(MangeCoursesListView, self).get_queryset()
        return qs.filter(owner=self.request.user)
