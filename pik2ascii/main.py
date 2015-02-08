import os
import urllib
import jinja2
import webapp2
import random
from bisect import bisect
from datetime import datetime
from datetime import time
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
from webapp2_extras import sessions
from PIL import Image
from cStringIO import StringIO

app_title         = 'PIK-2-ASCII'
ascii_data        = ''
message           = ''
form_status       = False
year              = datetime.now().strftime("%Y")
footer_text       = "All Rights Reserved "+ year  
JINJA_ENVIRONMENT = jinja2.Environment(
                            loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                            extensions=['jinja2.ext.autoescape'],
                            autoescape=True)

class Home(webapp2.RequestHandler):
    def get(self):                  
        upload_url = blobstore.create_upload_url('/convert')
        
        if ascii_data != '':
            form_status = True
        else:
            form_status = False                           
        
        template_values = {
            'app_title'   : app_title,
            'ascii_data'  : ascii_data,
            'message'     : app_title,
            'form_status' : form_status,
            'upload_url'  : upload_url
        }           
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))            
          
class ImageUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):     
        upload_files = self.get_uploads('starterImage')
        if upload_files:
            blob_info             = upload_files[0]
            key                   = blob_info.key()     
            self.redirect('/do/%s' % key)         
        else:
            self.redirect('/')
        
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        key                   = blob_info.key()
        blob_reader           = blobstore.BlobReader(key)            
        ascii                 = myAscii()
        ascii.image_obj       = blob_reader  
        ascii_data            = ascii.convert()            
        form_status           = True
        filename              = blob_info.filename
        filename = os.path.splitext(filename)[0]
        upload_url            = blobstore.create_upload_url('/convert')
        template_values = {
            'app_title'   : app_title,
            'ascii_data'  : ascii_data,
            'message'     : app_title,
            'form_status' : form_status,
            'upload_url'  : upload_url,
            'filename'    : filename
        }           
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
                             
class myAscii():    
    image_obj = None
    
    # greyscale.. the following strings represent
    # 7 tonal ranges, from lighter to darker.
    # for a given pixel tonal level, choose a character
    # at random from that range.
    greyscale = [
                " ",
                " ",
                ".,-",
                "_ivc=!/|\\~",
                "gjez2]/(YL)t[+T7Vf",
                "mdK4ZGbNDXY5P*Q",
                "W8KMA",
                "#%$"
                ]
     
    # using the bisect class to put luminosity values
    # in various ranges.
    # these are the luminosity cut-off points for each
    # of the 7 tonal levels. At the moment, these are 7 bands
    # of even width, but they could be changed to boost
    # contrast or change gamma, for example.
    zonebounds=[36,72,108,144,180,216,252]
    
    #
    size = 100,100
     
    def convert(self): 
        # open image and resize
        # experiment with aspect ratios according to font
        im = Image.open(self.image_obj,'r')
#         im = im.thumbnail(self.size, Image.ANTIALIAS)
        im = im.resize(self.size, Image.ANTIALIAS)
        im = im.convert("L") # convert to mono
         
        # now, work our way over the pixels
        # build up str
         
        str=""
        for y in range(0,im.size[1]):
            for x in range(0,im.size[0]):
                lum       = 255-im.getpixel((x,y))
                row       = bisect(self.zonebounds,lum)
                possibles = self.greyscale[row]
                str       = str+possibles[random.randint(0,len(possibles)-1)]
            str=str+"\n"
         
        return str


application = webapp.WSGIApplication([('/', Home),
                                      ('/convert', ImageUploadHandler),
                                      ('/do/([^/]+)?', ServeHandler)], 
                                     debug=False)       

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()