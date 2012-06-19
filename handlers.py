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
TEMPLATE_DIRS = [
   os.path.abspath(os.path.join(BASE_DIR, dir))
   for dir in ('thegrandlocus_theme', 'templates')
]


def enforce_login(parent):
   """Convenience function to enforce user log-in."""
   # Get user login status.
   user = users.get_current_user()
   if user:
      return user
   else:
      # User is not logged in... Go log in then.
      parent.redirect(users.create_login_url(parent.request.uri))


def get_new_entity_id(entity):
   """Return the id for a new entity."""
   model = {
      'plasmid': models.Plasmid(),
      'prep':    models.Prep(),
   }
   try:
      last_entity = model[entity].gql("ORDER BY id DESC LIMIT 1")[0]
      return 1 + last_entity.id
   except IndexError:
      return 1


def get_str_id(plasmid_id):
   """Return the str_id of for a new Prep object."""
   QUERY = "WHERE plasmid_id = :1 ORDER BY id DESC LIMIT 1"
   try:
      last_entity = models.Prep().gql(QUERY, plasmid_id)[0]
      _id = 1 + last_entity.id
   except IndexError:
      _id = 1
   return '%s-%s' % (plasmid_id, '-ABCDEFGHIJKLMNOPQRSTUVWXYZ'[_id])


# Django forms objects.
class PlasmidForm(djangoforms.ModelForm):
   name = forms.CharField(
       widget = forms.TextInput(attrs={'id':'name', 'class':'input'})
   )
   seq = forms.CharField(
       widget = forms.Textarea(
           attrs = {'id':'seq', 'rows':10, 'cols':20, 'class':'input'}
       )
   )
   comments = forms.CharField(
       widget = forms.Textarea(
           attrs = {'id':'comments', 'rows':10, 'cols':20, 'class':'input'}
       )
   )
   features = forms.CharField(
       widget = forms.Textarea(
           attrs = {'id':'features', 'rows':10, 'cols':20, 'class':'input'}
       )
   )

   class Meta:
      model = models.Plasmid
      fields = ['name', 'seq', 'comments', 'features']

class PrepForm(djangoforms.ModelForm):
   plasmid_id = forms.CharField(
       widget = forms.TextInput(attrs={'id':'plasmid_id', 'class':'input'})
   )
   comments = forms.CharField(
       widget = forms.Textarea(
           attrs = {'id':'comments', 'rows':10, 'cols':20, 'class':'input'}
       )
   )

   class Meta:
      model = models.Prep
      fields = ['plasmid_id', 'comments']


# Request handlers.
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


class ListingHandler(TemplateHandler):


   def get(self):
      prep_count = models.Prep().all().count()
      preps = models.Prep().all().fetch(prep_count)

      # Create a record class.
      class record:
         pass

      record_list = []
      for prep in preps:
         rec = record()
         rec.prep = prep
         rec.plasmid = models.Plasmid.get_by_key_name(str(prep.plasmid_id))
         record_list.append(rec)
      template_vals = { 'record_list': record_list }
      self.template_render('prep_listing.html', template_vals)


class NewPrepHandler(TemplateHandler):

   def get(self):
      """Handle new prep form query."""
      enforce_login(self)
      template_vals = {
         'form': PrepForm(),
         'entity': 'prep',
         'message': None,
      }
      self.template_render('new_entity.html', template_vals)

   def post(self):
      """Handle new prep data post."""
      enforce_login(self)
      id = get_new_entity_id('prep')
      plasmid_id = self.request.get('plasmid_id')
      str_id = get_str_id(self.request.get('plasmid_id'))
      new_prep = models.Prep(
          key_name = str(id),
          id = id,
          plasmid_id = plasmid_id,
          str_id = str_id,
	  comments = self.request.get('comments')
      )
      new_prep.put()
      message = 'Prep %s stored to the database.' % str_id,

      template_vals = {
         'form': PrepForm(),
         'entity': 'prep',
         'message': message,
      }
      self.template_render('new_entity.html', template_vals)


class NewPlasmidHandler(TemplateHandler):

   def get(self):
      """Handle new plasmid form query."""
      enforce_login(self)
      template_vals = {
         'form': PlasmidForm(),
         'entity': 'plasmid',
         'message': None,
      }
      self.template_render('new_entity.html', template_vals)

   def post(self):
      """Handle new plasmid data post."""
      enforce_login(self)
      id = get_new_entity_id('plasmid')
      new_plasmid = models.Plasmid(
          key_name = str(id),
          id = id,
	  name = self.request.get('name'),
	  seq = self.request.get('seq'),
	  comments = self.request.get('comments'),
	  features = str(self.request.get('features'))
      )
      new_plasmid.put()
      template_vals = {
         'form': PlasmidForm(),
         'entity': 'plasmid',
         'message': 'Plasmid #%d stored to the database.' % id,
      }
      self.template_render('new_entity.html', template_vals)

class PlasmidHandler(TemplateHandler):
   def get(self, path):
      plasmid = models.Plasmid.get_by_key_name(path)
      if not plasmid:
         self.template_render('404.html', {})
         return
      template_vals = {
         'plasmid': plasmid,
      }
      self.template_render('plasmid.html', template_vals)

class PrepHandler(TemplateHandler):
   def get(self, path):
      prep = models.Prep.get_by_key_name(path)
      if not prep:
         self.template_render('404.html', {})
         return
      plasmid = models.Plasmid.get_by_key_name(str(prep.plasmid_id))
      template_vals = {
         'prep': prep,
         'plasmid': plasmid,
      }
      self.template_render('prep.html', template_vals)

        
