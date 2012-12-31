import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


from google.appengine.ext import db


class Greeting(db.Model):
  """Models an individual Guestbook entry with content and date."""
  content = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)


def func(request):
	greeting = Greeting(content="helloa kskd")
	greeting.put()
	key = str(greeting.key())
	from django import http
	return http.HttpResponse("Entity saved with key "+key)
