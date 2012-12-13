# -*- coding: utf-8 -*-

from django.forms import ModelForm
from models import Backlog, Task

class BacklogForm(ModelForm):
    class Meta:
        model = Backlog
        exclude = ('product')
        
class TaskForm(ModelForm):
    class Meta:
        model = Task
        exclude = ('item')