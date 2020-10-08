from django.forms.models import inlineformset_factory
from .models import Course, Module


# courses have many modules so we need group of forms
# here we connect Courses and Modules
ModuleFormSet = inlineformset_factory(Course,
                                      Module,
                                      # in fields every variable will be in form
                                      fields=['title', 'description'],
                                      # how many empty forms wil be on page
                                      extra=2,
                                      can_delete=True)
