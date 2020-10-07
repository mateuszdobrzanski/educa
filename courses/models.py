from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


# General category of course
class Subject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['title', ]

    def __str__(self):
        return self.title


# each subject have multiple courses
class Course(models.Model):
    owner = models.ForeignKey(User,
                              related_name='courses_created',
                              on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject,
                                related_name='courses',
                                on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created', ]

    def __str__(self):
        return self.title


# in every course we can have multiple modules
class Module(models.Model):
    course = models.ForeignKey(Course,
                               related_name="modules",
                               on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title


# this class/model can handle different types for each module
# also this class have generic relationship for bind objects from different types and models
class Content(models.Model):
    module = models.ForeignKey(Module,
                               related_name="contents",
                               on_delete=models.CASCADE)
    # show ContentType in model
    content_type = models.ForeignKey(ContentType,
                                     on_delete=models.CASCADE)
    # handle bound model's PK
    object_id = models.PositiveIntegerField()
    # get bound object using object_id and content_type
    item = GenericForeignKey('content_type', object_id)
