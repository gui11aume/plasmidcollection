# -*- coding: utf-8 -*-

import setup_django_version

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django import forms
from google.appengine.ext.db import djangoforms

import handlers


application = webapp.WSGIApplication([
  ('/.*', handlers.TemplateHandler),
])


def main():
   run_wsgi_app(application)


if __name__ == '__main__':
    main()
