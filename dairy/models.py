from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User

# Create your models here.

# create a models for token sign up
@receiver(post_save,sender =settings.AUTH_USER_MODEL)
def create_auth_token(sender,instance = None, created = False,**kwargs) :
    if created :
        Token.objects.create(user = instance)

# New MyPage model
class MyPage(models.Model):
    username = models.CharField(max_length=150)
    image = models.ImageField(upload_to='mypage_images/', null=True, blank=True)
    upload_time = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return f"{self.username}'s page - {self.upload_time}"


class AdsImage(models.Model):
    image_path = models.CharField(max_length=2000)
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ad Image path added at {self.upload_time}"
    

class ContactForm(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"



class SecurityQuestion(models.Model):
    username = models.CharField(max_length=150)
    primary_school = models.CharField(max_length=200)
    favorite_color = models.CharField(max_length=100)
    pet_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Security Questions for {self.username}"
