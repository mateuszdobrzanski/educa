from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .fields import OrderField


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

    # the order depends on the course
    order = OrderField(blank=True, for_fields=['course'])

    class Meta:
        ordering = ['order']

    def __str__(self):
        return '{}. {}'.format(self.order, self.title)


# this class/model can handle different types for each module
# also this class have generic relationship for bind objects from different types and models
class Content(models.Model):
    module = models.ForeignKey(Module,
                               related_name="contents",
                               on_delete=models.CASCADE)
    # show ContentType in model
    content_type = models.ForeignKey(ContentType,
                                     limit_choices_to={'model__in': ('text',
                                                                     'video',
                                                                     'image',
                                                                     'file')},
                                     on_delete=models.CASCADE)
    # handle bound model's PK
    object_id = models.PositiveIntegerField()
    # get bound object using object_id and content_type
    item = GenericForeignKey('content_type', 'object_id')

    # the order depends on the module
    order = OrderField(blank=True, for_fields=['module'])

    class Meta:
        ordering = ['order']


# abstract model for all types to handle data
class ItemBase(models.Model):
    owner = models.ForeignKey(User,
                              # we reserved name in db for the class which we will build as extend ItemBase
                              related_name='%(class)s_related',
                              on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        # this mean the ItemBase class is abstract
        abstract = True

    def __str__(self):
        return self.title


# bellow we use abstract class ItemBase to build another classes
class Text(ItemBase):
    content = models.TextField()


class File(ItemBase):
    file = models.FileField(upload_to='files')


class Image(ItemBase):
    image = models.ImageField(upload_to='images')


class Video(ItemBase):
    url = models.URLField()
