# -*- coding: utf-8 -*-

from django.forms import ModelForm, DateTimeInput
from models import Sprint

class SprintEditForm(ModelForm):
    class Meta:
        model = Sprint
        fields = ('number','goal','timebox','start','end','demotime','dailytime','dailyroom','memo','status')
        widgets = {
            'start': DateTimeInput(), 'end': DateTimeInput(), 'demotime': DateTimeInput(),
        }
        #exclude = ('product','number','master','timebox','end','estimate','actual','review','retro','memo')
#    def clean(self):
#        """ Auto-fill self.end with start + timebox including weekends.
#        """
#        cleaned_data = self.cleaned_data
#        timebox = cleaned_data.get('timebox')
#        start = cleaned_data.get('start')
#        end = start
#        ds = 0
#        while ds < timebox:
#            if end.weekday() < 5:
#                ds += 1
#            end = end + timedelta(days=1)
#        self.cleaned_data['end'] = end
#        return cleaned_data
#    
