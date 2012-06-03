from google.appengine.ext import db

class Plasmid(db.Model):
   creation_date = db.DateTimeProperty(auto_now_add=True) 
   plasmid_id = db.IntegerProperty()
   name = db.StringProperty()
   seq = db.TextProperty()
   comments = db.TextProperty()
   features = db.BlobProperty()

   @property
   def location_tupe(self):
      x = self.plasmid_id - 1
      # Write 'x' in base 9: 81*a + 9*b + c.
      a = (x) / 81
      b = (x - 81*a) / 9
      c = (x - 81*a - 9*b)
      return (a+1, b+1, c+1)

   @property
   def location_string(self):
      (box, row, col) = self.location_tupe()

      return '%(box)d-%(row)s%(col)d' % {
         'box': box,
         'col': col,
         'row': '-ABCDEGFHI'[row]
      }
