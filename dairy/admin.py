from django.contrib import admin
from .models import MyPage, AdsImage, ContactForm, SecurityQuestion

# Register your models here.
admin.site.register(MyPage)
admin.site.register(AdsImage)
admin.site.register(ContactForm)
admin.site.register(SecurityQuestion)

