from google.appengine.ext import db

class Plasmid(db.Model):
   creation_date = db.DateTimeProperty(auto_now_add=False) 
   plasmid_id = db.IntegerProperty()
   box_num = db.IntegerProperty()
   row_num = db.IntegerProperty()
   col_num = db.IntegerProperty()
   name = db.StringProperty()
   seq = db.TextProperty()
   comments = db.TextProperty()
   features = db.BlobProperty()

   @property
   def row_char(self):
      return { 1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E',
               6: 'F', 7: 'G', 8: 'H', 9: 'I' }.get(self.row, '#')

   @property
   def location(self):
      return '%(box)d-%(row)s%(col)d' % {
         'box': self.box_num,
         'row': self.row_char,
         'col': self.col_num
      }
