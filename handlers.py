# -*- coding: utf-8 -*-

import setup_django_version

import os

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.db import djangoforms
from google.appengine.ext.webapp.template import _swap_settings

from django import forms
from django import template
from django.template import loader

import models


BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIRS = [os.path.abspath(os.path.join(BASE_DIR, 'templates'))]


def enforce_login(parent):
   """Convenience function to user log-in."""
   # Get user login status.
   user = users.get_current_user()
   if user:
      return user
   else:
      # User is not logged in... Go log in then.
      parent.redirect(users.create_login_url(parent.request.uri))


class PostForm(djangoforms.ModelForm):
   name = forms.CharField(
       widget = forms.TextInput(attrs={'id':'name'})
   )
   seq = forms.CharField(
       widget = forms.Textarea(
           attrs = {'id':'seq', 'rows':10, 'cols':20}
       )
   )
   comments = forms.CharField(
       widget = forms.Textarea(
           attrs = {'id':'comments', 'rows':10, 'cols':20}
       )
   )
   features = forms.CharField(
       widget = forms.Textarea(
           attrs = {'id':'features', 'rows':10, 'cols':20}
       )
   )

   class Meta:
      model = models.Plasmid
      fields = ['name', 'seq', 'comments', 'features']



class TemplateHandler(webapp.RequestHandler):
   """A base handler to implement Django template rendering."""

   def template_render(self, template_name, template_vals={}):
      """Render a given Django template with values and send
      the response."""

      # Add 'template_name' to values.
      template_vals.update({'template_name': template_name})
      old_settings = _swap_settings({'TEMPLATE_DIRS': TEMPLATE_DIRS})
      try:
         # Make a 'Template' object from file and render it.
         tpl = loader.get_template(template_name)
         # 'rendered' has class 'django.utils.safestring.SafeUnicode'.
         rendered = tpl.render(template.Context(template_vals))
      finally:
         _swap_settings(old_settings)

      self.response.out.write(rendered)

   def get(self):
      enforce_login(self)
      form = PostForm()
      self.template_render('base.html', { 'form':form })
