# -*- coding:utf-8 -*-

import setup_django_version

import os
import re
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
     ),
     required = False
   )
   comments = forms.CharField(
     widget = forms.Textarea(
       attrs = {'id':'comments', 'rows':10, 'cols':20, 'class':'input'}
     ),
     required = False
   )

   def clean_seq(self):
      data = self.cleaned_data['seq'].upper()
      return re.sub('[^GATCN]', '', data)

   class Meta:
      model = models.Plasmid
      fields = ['name', 'seq', 'comments']


class PrepForm(djangoforms.ModelForm):
   plasmid_id = forms.IntegerField(
     widget = forms.TextInput(attrs={'id':'plasmid_id', 'class':'input'})
   )
   comments = forms.CharField(
     widget = forms.Textarea(
       attrs = {'id':'comments', 'rows':10, 'cols':20, 'class':'input'}
     ),
     required = False
   )

   def clean_plasmid_id(self):
      data = self.cleaned_data['plasmid_id']
      # Raises an Exception if plasmid does not exist.
      if models.Plasmid.get_by_key_name(str(data)) is None:
         raise forms.ValidationError('Plasmid does not exist.')
      return data

   class Meta:
      model = models.Prep
      fields = ['plasmid_id', 'comments']

class FeatureForm(djangoforms.ModelForm):
   name = forms.CharField(
     widget = forms.TextInput(attrs={'id':'name', 'class':'input'})
   )

   start = forms.IntegerField(
     widget = forms.TextInput(
       attrs = {'id':'start', 'class':'input'}
     )
   )

   end = forms.IntegerField(
     widget = forms.TextInput(
       attrs = {'id':'end', 'class':'input'}
     )
   )

   orientation = forms.ChoiceField(
      choices = (('+','+'), ('-','-')),
      initial = '+'
   )

   ftype = forms.ChoiceField(
      choices = ((ft,ft) for ft in config.ftypes),
      label = 'Type'
   )


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

      plasmid_name_by_id = dict(
        [(plasmid.nid, plasmid.name) for plasmid in plasmid_list]
      )

      for prep in prep_list:
         prep.plasmid_name = plasmid_name_by_id[prep.plasmid_id]

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
      user = users.get_current_user()
      if user is None:
         self.redirect(users.create_login_url(self.request.uri))
         return

      template_vals = {
         'form': PrepForm(),
         'entity': 'prep',
         'message': None,
      }
      self.template_render('new_entity.html', template_vals)

   def post(self):
      """Handle new prep data post."""
      user = users.get_current_user()
      if user is None:
         self.redirect(users.create_login_url(self.request.uri))
         return
      if not utils.is_editor(user):
         # Error 401, user is not authorized.
         self.error(401)
         self.template_render('401.html')
         return

      form = PrepForm(data=self.request.POST)

      if form.is_valid():
         plasmid_id = form.cleaned_data['plasmid_id']
         comments = form.cleaned_data['comments']
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
      else:
         template_vals = {
            'form': form,
            'entity': 'prep',
            'message': ''
         }

      self.template_render('new_entity.html', template_vals)


class NewPlasmidHandler(TemplateHandler):
   def get(self):
      """Handle new plasmid form query."""
      user = users.get_current_user()
      if user is None:
         self.redirect(users.create_login_url(self.request.uri))
         return

      template_vals = {
         'form': PlasmidForm(),
         'entity': 'plasmid',
         'message': None,
      }
      self.template_render('new_entity.html', template_vals)

   def post(self):
      """Handle new plasmid data post."""
      user = users.get_current_user()
      if user is None:
         self.redirect(users.create_login_url(self.request.uri))
         return

      if not utils.is_editor(user):
         # Error 401, user is not authorized.
         self.error(401)
         self.template_render('401.html', {})
         return

      form = PlasmidForm(data=self.request.POST)

      if form.is_valid():
         name = form.cleaned_data['name']
         seq = form.cleaned_data['seq']
         comments = form.cleaned_data['comments']

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
         message = 'Plasmid #%d has been stored.' % nid

         template_vals = {
            'form': PlasmidForm(),
            'entity': 'plasmid',
            'message': message,
         }

      else:
         template_vals = {
            'form': form,
            'entity': 'plasmid',
            'message': ''
         }

      self.template_render('new_entity.html', template_vals)


class PlasmidHandler(TemplateHandler):
   def get(self, path):
      user = users.get_current_user()

      plasmid = models.Plasmid.get_by_key_name(path)
      if not plasmid:
         self.template_render('404.html', {})
         return

      features = json.loads(plasmid.features)

      template_vals = {
         'plasmid': plasmid,
         'zip_features': enumerate(features),
         'can_edit': user and utils.is_editor(user),
         'form': FeatureForm()
      }
      self.template_render('plasmid.html', template_vals)

   def post(self, path):
      user = users.get_current_user()
      if user is None:
         self.redirect(users.create_login_url(self.request.uri))
         return

      if not utils.is_editor(user):
         # Error 401, user is not authorized.
         self.error(401)
         self.template_render('401.html', {})
         return

      plasmid = models.Plasmid.get_by_key_name(path)
      features = json.loads(plasmid.features)

      # Check if this is a delete request.
      if self.request.get('delete', None) is None:
         # It is a new feature request.
         form = FeatureForm(data=self.request.POST)
         if form.is_valid():
            features.append({
              'name': form.cleaned_data['name'],
              'start': form.cleaned_data['start'],
              'end': form.cleaned_data['end'],
              'orientation': form.cleaned_data['orientation'],
              'ftype': form.cleaned_data['ftype'],
            })
            # Save feature to data store.
            plasmid.features = json.dumps(features)
            plasmid.put()
            # Clean form.
            form = FeatureForm()
      else:
         # It is a delete request.
         delete_feature = int(self.request.get('delete'))
         features.pop(delete_feature)
         plasmid.features = json.dumps(features)
         plasmid.put()
         form = FeatureForm()

      template_vals = {
         'plasmid': plasmid,
         'zip_features': enumerate(features),
         'can_edit': utils.is_editor(users.get_current_user()),
         'form': form,
      }
      self.template_render('plasmid.html', template_vals)
