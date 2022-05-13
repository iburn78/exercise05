from PIL import Image, ImageOps
from django.conf import settings
import os
from io import BytesIO
from django.core.files.base import ContentFile
from datetime import datetime
POST_IMG_MAXSIZE = 2000


def image_resize(maxsize, img: Image) -> Image:
  w, h = img.size
  if w <= h: 
    if h <= maxsize: 
      res = img
    else: 
      wr = round(w/h*maxsize)
      hr = maxsize
      res = img.resize((wr, hr))
  else: 
    if w <= maxsize:
      res = img
    else: 
      wr = maxsize
      hr = round(h/w*maxsize)
      res = img.resize((wr, hr))
  return res

def post_image_resize(post) -> None:
  images = [post.image1, post.image2, post.image3, post.image4, post.image5, post.image6, post.image7]
  th_images = [post.image1s, post.image2s, post.image3s, post.image4s, post.image5s, post.image6s, post.image7s]
  for i in range(0, 7):
    try:
      if th_images[i].name != "":
        th_images[i].delete()
    except:
      text = "Exception in delete images - def post_image_resize: "+ th_images[i].name  
      exception_log(text)

  if post.num_images == 0: 
    return None

  wa = []
  ha = []
  hh = []
  wh = []
  for i in range(0, post.num_images): 
    with Image.open(images[i].file) as img:
      img = ImageOps.exif_transpose(img)
      w, h = img.size
      wa.append(w)
      ha.append(h)
      hh.append(h*h)
      wh.append(w*h)
    

  try:
    ar = float(sum(hh)/sum(wh))
  except: 
    text = "Exception in ar calc. - def post_image_resize: "+ th_images[i].name  
    exception_log(text)
    ar = 1

  croparea = []
  for i in range(0, post.num_images): 
    w = wa[i]
    h = ha[i]
    if ar >= h/w:
      croparea.append(((w-h/ar)/2, 0, (w+h/ar)/2, h))
    else: 
      croparea.append((0, (h-w*ar)/2, w, (h+w*ar)/2))


  for i in range(0, post.num_images): 
    img_io = BytesIO()
    exception_log('step 1')
    img = Image.open(images[i].file)
    exception_log('step 2')
    img_exif = ImageOps.exif_transpose(img)
    exception_log('step 3')
    res = img_exif.crop(croparea[i])
    exception_log('step 4')
    res = image_resize(POST_IMG_MAXSIZE, res)
    exception_log('step 5')
    res.save(img_io, format=img.format)
    exception_log('step 6')
    th_images[i].save(os.path.basename(images[i].file.name), ContentFile(img_io.getvalue()))
    exception_log('step 7')
  

def exception_log(text): 
  print("--------------->>>>>>")
  print(text)
  logfilepath = os.path.join(settings.BASE_DIR, 'etc') 
  with open(os.path.join(logfilepath, 'exception_log.txt'), 'a') as logfile: 
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    logfile.write(now + " " + text + "\n")


# from pathlib import Path
# import json
# import os

# BASE_DIR = Path(__file__).resolve().parent.parent
# i1 = Image.open(os.path.join(BASE_DIR,'media/temp/background.jpg'))
# i2 = Image.open(os.path.join(BASE_DIR,'media/temp/cap.JPG'))
# i3 = Image.open(os.path.join(BASE_DIR,'media/temp/xooos.JPG'))

# wa = []
# ha = []
# hh = []
# wh = []
# for i in [i1, i2, i3]:
#   w, h = i.size
#   print('before')
#   print(w,h)
#   img = ImageOps.exif_transpose(i)
#   w, h = img.size
#   print('after')
#   print(w,h)
#   wa.append(w)
#   ha.append(h)
#   hh.append(h*h)
#   wh.append(w*h)

# ar = float(sum(hh)/sum(wh))

# for i in [i1, i2, i3]:
#   w, h = img.size
#   if ar >= h/w:
#     croparea = ((w-h/ar)/2, 0, (w+h/ar)/2, h)
#   else: 
#     croparea = (0, (h-w*ar)/2, w, (h+w*ar)/2)
#   print(ar)
#   print(croparea)
