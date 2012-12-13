# -*- coding: utf-8 -*-

from django.contrib import admin
from models import Backlog, Task, Hierarchy

admin.site.register(Backlog)
admin.site.register(Task)
admin.site.register(Hierarchy)
