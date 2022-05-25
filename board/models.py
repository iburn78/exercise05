from django.db import models
from django.utils import timezone
from django.urls import reverse
from taggit.managers import TaggableManager
from users.models import User
from board.tools import *
import os
from django.conf import settings
from random import choice
from os.path import join as path_join
from os import listdir
from os.path import isfile

# Important concepts:
# - public card / public posts (vs private, by default)
# - approved user to use key features
# - linking cards
# - publishing posts
# - importing posts
# - comments in published posts
# - tags


def filename_gen_userid(userid, filename):
    userid = str(userid)
    res = ""
    for ch in userid:
        res += str(ord(ch))
    return res[:7]+"_"+filename

def filename_gen_randomize(userid, filename):
    res = str(abs(hash(str(userid))))
    return res[:7]+"_"+filename

def path_to_card_imgs(instance, filename):
    if instance.is_public == True: 
        path = CARD_PUBLIC_UPLOADED_IMGS
        newname = filename_gen_randomize(instance.owner, filename)
    else:
        path = CARD_UPLOADED_IMGS
        newname = filename_gen_userid(instance.owner, filename)
    return os.path.join(path, newname)


def path_to_imgs(instance, filename):
    if instance.card.is_public: 
        path = POST_PUBLIC_UPLOADED_IMGS
        newname = filename_gen_randomize(instance.author, filename)
    else:
        path = POST_UPLOADED_IMGS
        newname = filename_gen_userid(instance.author, filename)
    return os.path.join(path, newname)


def path_to_imgs_th(instance, filename):
    if instance.card.is_public: 
        path = POST_PUBLIC_UPLOADED_IMGS_RESIZED
    else:
        path = POST_UPLOADED_IMGS_RESIZED
    return os.path.join(path, filename)


def random_img():
    dir_path = path_join(settings.MEDIA_ROOT, CARD_DEFAULT_IMAGES)
    print(listdir(dir_path))
    files = [content for content in listdir(dir_path) if isfile(path_join(dir_path, content))]
    print(files)
    return path_join(dir_path, choice(files))


class Card(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=70)
    desc = models.TextField(blank=True)
    image = models.ImageField(default=random_img, upload_to=path_to_card_imgs)
    card_color = models.CharField(
        max_length=30, default='rgb(233, 236, 239)')  # gray-200
    is_public = models.BooleanField(default=False)
    # for id of a public card / can link only one card
    linked_card = models.CharField(max_length=10, blank=True)

    # Rules
    # only admin users can make a card public
    # linking a card: a user can link a public card to his/her own card

    def delete(self, *args, **kwargs):
        name = str(self.image.name)
        try:
            image_path = os.path.basename(os.path.dirname(self.image.name))
            path_check_private = os.path.basename(CARD_UPLOADED_IMGS)
            path_check_public = os.path.basename(CARD_PUBLIC_UPLOADED_IMGS)
            if image_path == path_check_private or image_path == path_check_public:
                self.image.delete()
        except:
            text = "Exception in deleting image - class Card delete(): " + name
            exception_log(text)
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('main')


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    date_posted = models.DateTimeField(default=timezone.now)
    content = models.TextField()
    num_images = models.IntegerField(default=0)
    image1 = models.ImageField(upload_to=path_to_imgs, blank=True)
    image2 = models.ImageField(upload_to=path_to_imgs, blank=True)
    image3 = models.ImageField(upload_to=path_to_imgs, blank=True)
    image4 = models.ImageField(upload_to=path_to_imgs, blank=True)
    image5 = models.ImageField(upload_to=path_to_imgs, blank=True)
    image6 = models.ImageField(upload_to=path_to_imgs, blank=True)
    image7 = models.ImageField(upload_to=path_to_imgs, blank=True)

    image1s = models.ImageField(upload_to=path_to_imgs_th, blank=True)
    image2s = models.ImageField(upload_to=path_to_imgs_th, blank=True)
    image3s = models.ImageField(upload_to=path_to_imgs_th, blank=True)
    image4s = models.ImageField(upload_to=path_to_imgs_th, blank=True)
    image5s = models.ImageField(upload_to=path_to_imgs_th, blank=True)
    image6s = models.ImageField(upload_to=path_to_imgs_th, blank=True)
    image7s = models.ImageField(upload_to=path_to_imgs_th, blank=True)

    tags = TaggableManager(blank=True)
    is_published = models.BooleanField(default=False)

    # Rules
    # publishing posts: posts can be published (only) to public cards, and posts in public cards must be (all) publised
    # importing posts: a user can import published posts to his/her own linked card

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        images = [self.image1, self.image2, self.image3, self.image4, self.image5, self.image6, self.image7]
        th_images = [self.image1s, self.image2s, self.image3s, self.image4s, self.image5s, self.image6s, self.image7s]
        for i in range(0, 7):
            try:
                if images[i].name != "":
                    images[i].delete()
            except:
                text = "Exception in delete images - class Post delete(): " + images[i].name
                exception_log(text)

            try:
                if th_images[i].name != "":
                    th_images[i].delete()
            except:
                text = "Exception in delete th_images - class Post delete(): " + th_images[i].name
                exception_log(text)

        return super().delete(*args, **kwargs)

    def get_preview_text(self):
        res = ' '.join(self.content[:150].split('\n')[:3])
        return res

    def __str__(self):
        return self.get_preview_text()

    class Meta:
        None

    def get_absolute_url(self):
        return reverse('card-content', kwargs={'card_id': self.card.id})
