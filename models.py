from google.appengine.ext import db
from google.appengine.api import users

class Plasmid(db.Model):
   creation_date = db.DateTimeProperty(auto_now_add=True) 
   creator = db.UserProperty(auto_current_user_add=True)
   id = db.IntegerProperty()
   name = db.StringProperty()
   seq = db.TextProperty()
   features = db.BlobProperty()
   comments = db.TextProperty()


class Prep(db.Model):
   creation_date = db.DateTimeProperty(auto_now_add=True)
   creator = db.UserProperty(auto_current_user_add=True)
   id = db.IntegerProperty()
   plasmid_id = db.IntegerProperty()
   str_id = db.StringProperty()
   comments = db.TextProperty()

   @property
   def location_tupe(self):
      x = self.prep_num_id - 1
      # Write 'x' in base 9: 81*a + 9*b + c.
      a = (x) / 81
      b = (x - 81*a) / 9
      c = (x - 81*a - 9*b)
      return (a+1, b+1, c+1)

   @property
   def location_string(self):
      (box, row, col) = self.location_tupe
      return '%(box)d-%(row)s%(col)d' % {
         'box': box,
         'col': col,
         'row': '-ABCDEGFHI'[row]
      }
