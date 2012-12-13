# -*- coding: utf-8 -*-

from django import forms
from django.utils.log import getLogger
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from models import SEX_CHOICES, ROLE_CHOICES, Staff, Team

logger = getLogger('Floret')

def get_teams():
    return tuple([('%s'%t.pk,t.name) for t in Team.objects.all()])

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=30, label=_('Username'), help_text=_('Unique username'))
    firstname = forms.CharField(label=_('First Name'),max_length=16,help_text=_('First name'))
    lastname = forms.CharField(label=_('Last Name'), max_length=16, help_text=_('Last name'))
    email = forms.EmailField(label=_('Email Address'), required=False, help_text=_('Email address'))
    password = forms.CharField(max_length=30,widget=forms.PasswordInput,label=_('Password'),help_text=_('Password'))
    password2 = forms.CharField(max_length=30,widget=forms.PasswordInput,label=_('Repeat password'),help_text=_('Repeat the password'))
    gender = forms.ChoiceField(widget=forms.RadioSelect,label=_('Gender'),choices=SEX_CHOICES,initial='M')
    role = forms.ChoiceField(label=_('User Role'),choices=ROLE_CHOICES, help_text=_('Developer, Product owner or Scrum master'))
    team = forms.ChoiceField(label=_('Team'), choices=get_teams(), required=False, help_text=_('Optionally select a team to join'))
    
    def set_error(self,name,value):
        self._errors[name] = value
        
    def clearn(self):
        cleaned_data = self.cleaned_data
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password != password2:
            msg = _('The passwords are not the same!')
            self._errors['password2'] = self.error_class([msg])
            del cleaned_data['password2']
        return cleaned_data

    def save(self):
        """ Save registration forms data into User and Staff.
            If any save operation fails, the others will be rolled back.
            @return: User instance
        """
        data = self.cleaned_data
        try:
            user = User(username=data['username'])
            user.email = data['email']
            user.set_password(data['password'])
            user.first_name = data['firstname']
            user.last_name = data['lastname']
            user.is_active = True
            user.save()
            if data['team']:
                try:
                    g = get_object_or_404(Group, pk=data['team'])
                    user.groups.add(g)
                except:
                    pass
            try:
                staff = Staff(user=user)
                staff.gender = data['gender']
                staff.role = data['role']
                staff.save()
                return user
            except Exception,e:
                logger.error('RegisterForm.save():%s'%e)
                user.delete()
                raise e
        except Exception,e:
            logger.error('RegisterForm.save():%s'%e)
            raise e

class StaffForm(forms.ModelForm):
    """ Staff only form """
    class Meta:
        model = Staff
        fields = ('gender','birthday','mobile','im','headshot')
#        exclude = ('user','role','product','level','points','stars','credits','hearts','online','skills')
    team = forms.ChoiceField(label=_('Team'), choices=get_teams(), required=False, help_text=_('Optionally select a team to join'))

class TeamForm(forms.ModelForm):
    """ Team and Group input form.
    """
    class Meta:
        model = Group
        exclude = ('permissions')
        
    intro = forms.CharField(max_length=256, label=_('Introduction'), widget=forms.TextInput)
    velocity = forms.FloatField(label=_('Velocity'), initial=10)
    
    def save(self):
        """ Save both Group and Team.
        """
        group = super(TeamForm, self).save()
        try:
            team = group.profile
            data = self.cleaned_data
            team.intro = data['intro']
            team.velocity = data['velocity']
            team.save()
            return group
        except:
            group.delete()
            return None
        