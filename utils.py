# -*- coding:utf-8 -*-

from hashlib import sha1

from google.appengine.api import users

import config
import models


class alternator:
   """Simple alternator to change table row styling in the
   Django template."""
   def __init__(self, objects):
      self.n_objects = len(objects)
      self.objects = objects
      self.current = -1
   @property
   def next(self):
      self.current += 1
      return self.objects[self.current % self.n_objects]


def enforce_login(parent):
   """Convenience function to enforce user log-in."""
   # Get user login status.
   user = users.get_current_user()
   if user:
      return user
   else:
      # User is not logged in... Go log in then.
      parent.redirect(users.create_login_url(parent.request.uri))

def is_admin(user):
   return sha1(user.email()).hexdigest() in config.administrators

def is_editor(user):
   return is_admin(user) or \
            sha1(user.email()).hexdigest() in config.authorized_editors


def get_new_entity_id(entity):
   """Return the id for a new entity."""
   model = {
      'plasmid': models.Plasmid(),
      'prep':    models.Prep(),
   }
   # Return 1 for the very first entry of an entity.
   try:
      last_entity = model[entity].gql("ORDER BY nid DESC LIMIT 1")[0]
      return 1 + last_entity.nid
   except IndexError:
      return 1


def get_str_id(plasmid_id):
   """Return the str_id of for a new Prep object."""
   QUERY = "WHERE plasmid_id = :1 ORDER BY nid DESC LIMIT 1"
   try:
      last_entity = models.Prep().gql(QUERY, plasmid_id)[0]
      nid = 1 + last_entity.nid
   except IndexError:
      nid = 1
   return '%d%s' % (plasmid_id, '-abcdefghijklmnopqrstuvwxyz'[nid])


