from __future__ import unicode_literals
from django.db import models
from home.constants import *
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class MyUser(AbstractUser):
    latitude = models.FloatField(null=True,)
    longitude = models.FloatField(null=True,)
    country = models.TextField(null=True, blank=True)
    holiday = models.TextField(null=True, blank=True)

class Post(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='author')
    body = models.TextField(blank=False)
    # liked = models.ManyToManyField(MyUser, default=None, blank=True, related_name='liked')
    active = models.BooleanField(blank=False)
    created_at = models.DateTimeField('%m/%d/%Y %H:%M:%S', auto_now_add=True)
    updated_at = models.DateTimeField('%m/%d/%Y %H:%M:%S', auto_now=True)

    def __str__(self):
        return str(self.body)


class Like(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    value = models.CharField(choices=LIKE_CHOICES, default='Like', max_length=10)

    class Meta:
        unique_together = [
            ['user', 'post', 'value']
        ]

    def __str__(self):
        return str(self.post)
