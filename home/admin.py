from django.contrib import admin
from home.models import *

# Register your models here.
admin.site.register(MyUser)
admin.site.register(Post)
admin.site.register(Like)