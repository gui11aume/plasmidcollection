# -*- coding:utf-8 -*-

import setup_django_version

import os
try:
   import json
except ImportError:
   import simplejson as json

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.db import djangoforms
from google.appengine.ext.webapp.template import _swap_settings

from django import forms
from django import template
from django.template import loader

import models
import config
import utils


BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIRS = [
   os.path.abspath(os.path.join(BASE_DIR, directory))
   for directory in ('thegrandlocus_theme/templates', 'templates')
]



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

   class Meta:
      model = models.Plasmid
      fields = ['name', 'seq', 'comments']


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
      plasmid_count = models.Plasmid().all().count()
      prep_list = models.Prep().all().fetch(prep_count)
      plasmid_list = models.Plasmid.all().fetch(plasmid_count)

      plasmid_by_id = dict(
        [(plasmid.nid, plasmid) for plasmid in plasmid_list]
      )

      for prep in prep_list:
         prep.plasmid_name = plasmid_by_id[prep.nid].name

      alt = utils.alternator(("odd", "even"))
      template_vals = {
        'plasmid_list': plasmid_list,
        'prep_list': prep_list,
        'alternator': alt
      }
      self.template_render('plasmid_collection_listing.html',
        template_vals)


class NewPrepHandler(TemplateHandler):
   def get(self):
      """Handle new prep form query."""
      utils.enforce_login(self)

      template_vals = {
         'form': PrepForm(),
         'entity': 'prep',
         'message': None,
      }
      self.template_render('new_entity.html', template_vals)

   def post(self):
      """Handle new prep data post."""
      user = utils.enforce_login(self)
      if not utils.is_editor(user):
         # Error 401, user is not authorized.
         self.error(401)
         self.template_render('401.html', {})
         return

      form = PrepForm(data=self.request.POST)
      if not form.is_valid():
         self.get()
         return

      plasmid_id = int(form.cleaned_data['plasmid_id'])
      comments = form.cleaned_data['comments']

      try:
         # Raises an Exception if plasmid does not exist.
         models.Plasmid.get_by_key_name(str(plasmid_id))
      except AttributeError:
         message = 'Specified plasmid does not exist.'
      except Exception, e:
         message = str(e)
         #message = 'Input error.'
      else:
         nid = utils.get_new_entity_id('prep')
         new_prep = models.Prep(
             key_name = str(nid),
             nid = nid,
             plasmid_id = plasmid_id,
             str_id = utils.get_str_id(plasmid_id),
             comments = comments
         )
         new_prep.put()
         message = 'Prep %s has been stored.' % new_prep.str_id

      template_vals = {
         'form': PrepForm(),
         'entity': 'prep',
         'message': message,
      }
      self.template_render('new_entity.html', template_vals)


class NewPlasmidHandler(TemplateHandler):
   def get(self):
      """Handle new plasmid form query."""
      utils.enforce_login(self)
      template_vals = {
         'form': PlasmidForm(),
         'entity': 'plasmid',
         'message': None,
      }
      self.template_render('new_entity.html', template_vals)

   def post(self):
      """Handle new plasmid data post."""
      user = utils.enforce_login(self)
      if not utils.is_editor(user):
         # Error 401, user is not authorized.
         self.error(401)
         self.template_render('401.html', {})
         return

      form = PlasmidForm(data=self.request.POST)
      if not form.is_valid():
         self.get()
         return

      name = form.cleaned_data['name']
      seq = form.cleaned_data['seq']
      comments = form.cleaned_data['comments']

      try:
         nid = utils.get_new_entity_id('plasmid')
         new_plasmid = models.Plasmid(
             key_name = str(nid),
             nid = nid,
             name = name,
             seq = seq,
             comments = comments,
             features = '[]'
         )
         new_plasmid.put()
      except Exception:
         message = 'Input error.'
      else:
         message = 'Plasmid #%d has been stored.' % nid

      template_vals = {
         'form': PlasmidForm(),
         'entity': 'plasmid',
         'message': message,
      }
      self.template_render('new_entity.html', template_vals)


class PlasmidHandler(TemplateHandler):
   def get(self, path):
      plasmid = models.Plasmid.get_by_key_name(path)
      if not plasmid:
         self.template_render('404.html', {})
         return

      try:
         features = json.loads(plasmid.features or '[]'),
      except Exception:
         features = []
         message = '** ERROR **'
      else:
         message = ''

      template_vals = {
         'message': message,
         'plasmid': plasmid,
         'features': features,
         'can_edit': utils.is_editor(users.get_current_user()),
      }
      self.template_render('plasmid.html', template_vals)


#class PrepHandler(TemplateHandler):
#   def get(self, path):
#      prep = models.Prep.get_by_key_name(path)
#      if not prep:
#         self.template_render('404.html', {})
#         return
#      plasmid = models.Plasmid.get_by_key_name(str(prep.plasmid_id))
#      template_vals = {
#         'prep': prep,
#         'plasmid': plasmid,
#      }
#      self.template_render('prep.html', template_vals)
