"""
URL configuration for dream project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from dairy import views
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('sign_up/', views.sign_up, name= 'sign_up'),
    path('login/', views.log_in, name= 'log_in'),


    path("token/",obtain_auth_token,name='token'),
    path('my-page/', views.MyPageView.as_view(), name='my_page'),
    path('logout/', views.logout, name='logout'),
    path('contact/', views.contact_us, name='contact_us'),
    path('about-us/', views.about_us, name='about_us'),
    path('page/<int:page_id>/', views.view_page_details, name='view_page_details'),

    path('user-details/', views.user_details, name='user_details'),
    path('delete-page/<int:page_id>/', views.delete_page, name='delete_page'),
    path('forget-password/', views.forget_password, name='forget_password'),
    path('security-questions/', views.security_questions, name='security_questions'),
    path('reset-password/<str:username>/', views.reset_password, name='reset_password'),
    path('verify-otp/<str:username>/', views.check_otp, name='check_otp'),
    path('send-otp/', views.send_otp, name='send_otp'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
