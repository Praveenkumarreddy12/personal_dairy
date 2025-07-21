from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User,auth
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import MyPageForm, SignUpForm, LoginForm, ContactForm
from .models import MyPage, AdsImage, SecurityQuestion
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.core.mail import send_mail, get_connection
from django.conf import settings
import random
import string
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Store username in session
            request.session['signup_username'] = user.username
            return redirect('security_questions')
    else:
        form = SignUpForm()
    return render(request, 'sign_up.html', {'form': form})

# to store token value instently
@csrf_exempt
def log_in(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = auth.authenticate(username=username, password=password)
            
            if user is not None:
                auth.login(request, user)
                # Delete any existing token
                Token.objects.filter(user=user).delete()
                # Create new token
                token = Token.objects.create(user=user)
                # Store token in session for easy access
                request.session['auth_token'] = token.key
                return redirect('my_page')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

class CustomTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        if (timezone.now() - token.created) > timedelta(hours=12):
            token.delete()
            raise AuthenticationFailed('Token has expired')

        return (token.user, token)

class MyPageView(View):
    def dispatch(self, request, *args, **kwargs):
        token_key = request.session.get('auth_token')
        if not token_key:
            return redirect('log_in')
        
        try:
            auth = CustomTokenAuthentication()
            user, token = auth.authenticate_credentials(token_key)
            request.user = user
            return super().dispatch(request, *args, **kwargs)
        except AuthenticationFailed:
            return redirect('log_in')

    def get(self, request):
        form = MyPageForm()
        entries = MyPage.objects.filter(username=request.user.username).order_by('-upload_time')
        return render(request, 'my_page.html', {'form': form, 'entries': entries})

    @csrf_exempt
    def post(self, request):
        form = MyPageForm(request.POST, request.FILES)
        if form.is_valid():
            my_page = form.save(commit=False)
            my_page.username = request.user.username
            my_page.save()
            return redirect('my_page')
        return render(request, 'my_page.html', {'form': form})

def home(request):
    ads_images = AdsImage.objects.all()
    return render(request, 'home.html', {'ads_images': ads_images})

def logout(request):
    if request.session.get('auth_token'):
        # Delete the token from database
        token_key = request.session['auth_token']
        Token.objects.filter(key=token_key).delete()
        # Remove token from session
        del request.session['auth_token']
    
    # Logout the user
    auth.logout(request)
    return redirect('home')
@csrf_exempt
def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()  # Save the form data to database
            return render(request, 'contact_us.html', {
                'form': ContactForm(),
                'success': True
            })
    else:
        form = ContactForm()
    
    return render(request, 'contact_us.html', {'form': form})

def about_us(request):
    context = {
        'title': 'About Us',
        'description': '''User Input Capabilities: The application allows users to upload an image and enter associated text. The image could be a photo, illustration, or any visual content, and the text could include descriptions, tags, comments, or other relevant details.

Features:

Image Upload: Users can select and upload images from their device.
Text Input: Users can provide a description, caption, or any other related text for the image.
Preview Option: Allows users to see a preview of the uploaded image along with the entered text.
File Type and Size Handling: Supports common image formats (JPEG, PNG, etc.) and restricts file sizes if needed.
Use Cases:

Photo Sharing: Users share images with captions, similar to social media platforms.
Documentation: Upload images for documentation purposes with detailed notes.
Image Tagging: Allow users to tag and categorize uploaded images with text descriptions.''',
        # Add any other context data you want to pass to the template
    }
    return render(request, 'about_us.html', context)


def user_details(request):
    if request.user.is_authenticated:
        try:
            # Get date filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            # Start with base query
            user_pages = MyPage.objects.filter(username=request.user.username)

            # Apply date filters if provided
            if start_date:
                user_pages = user_pages.filter(upload_time__gte=start_date)
            if end_date:
                user_pages = user_pages.filter(upload_time__lte=end_date)

            # Order by upload time
            user_pages = user_pages.order_by('-upload_time')
            
            # Prepare user details
            user_details = {
                'username': request.user.username,
                'pages': [{
                    'image': page.image.url if page.image else None,
                    'content': page.content,
                    'upload_time': page.upload_time,
                    'id': page.id,
                } for page in user_pages]
            }
            
            return render(request, 'specific_img.html', {'user_details': user_details})
            
        except MyPage.DoesNotExist:
            return render(request, 'specific_img.html', {
                'error': 'No pages found for this user'
            })
    else:
        return render(request, 'specific_img.html', {
            'error': 'Please log in to view your pages'
        })


def delete_page(request, page_id):
    if not request.user.is_authenticated:
        return redirect('log_in')
    
    try:
        # Only allow users to delete their own pages
        page = MyPage.objects.get(id=page_id, username=request.user.username)
        page.delete()
        return redirect('user_details')
    except MyPage.DoesNotExist:
        # Handle case where page doesn't exist or doesn't belong to user
        return render(request, 'specific_img.html', {
            'error': 'Page not found or you do not have permission to delete it'
        })


def view_page_details(request, page_id):
    if not request.user.is_authenticated:
        return redirect('log_in')
        
    try:
        # Get all pages for the logged in user ordered by upload time
        user_pages = MyPage.objects.filter(username=request.user.username).order_by('upload_time')
        
        # Get the current page and its index
        current_page = MyPage.objects.get(id=page_id, username=request.user.username)
        current_index = list(user_pages.values_list('id', flat=True)).index(current_page.id)
        
        # Get next and previous page IDs if they exist
        next_id = None
        prev_id = None
        if current_index < len(user_pages) - 1:
            next_id = user_pages[current_index + 1].id
        if current_index > 0:
            prev_id = user_pages[current_index - 1].id
            
        page_details = {
            'image': current_page.image.url if current_page.image else None,
            'content': current_page.content,
            'upload_time': current_page.upload_time,
            'username': current_page.username,
            'id': current_page.id,
            'next_id': next_id,
            'prev_id': prev_id,
            'total_pages': len(user_pages),
            'current_page': current_index + 1
        }
        
        return render(request, 'one_img.html', {'page_details': page_details})
        
    except MyPage.DoesNotExist:
        return render(request, 'one_img.html', {
            'error': 'Page not found or you do not have permission to view it'
        })


def ads_image(request):
    ads_images = AdsImage.objects.all()
    return render(request, 'ads_image.html', {'ads_images': ads_images})

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@csrf_exempt
def forget_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        primary_school = request.POST.get('primary_school')
        favorite_color = request.POST.get('favorite_color')
        pet_name = request.POST.get('pet_name')

        try:
            # Get the security questions for this username
            security_qa = SecurityQuestion.objects.get(username=username)
            
            # Compare answers
            if (security_qa.primary_school.lower() == primary_school.lower() and 
                security_qa.favorite_color.lower() == favorite_color.lower() and 
                security_qa.pet_name.lower() == pet_name.lower()):
                
                # If answers match, redirect to reset password view with username
                return redirect('reset_password', username=username)
            else:
                messages.error(request, 'Security answers do not match.')
                return redirect('forget_password')
                
        except SecurityQuestion.DoesNotExist:
            messages.error(request, 'No security questions found for this username.')
            return redirect('forget_password')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forget_password')
            
    return render(request, 'forget.html')

@csrf_exempt
def send_otp(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            otp = generate_otp()
            subject = 'OTP for Password Reset'
            message = f'Your OTP for password reset is: {otp}'
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False,)
            request.session['otp'] = otp  # Add otp to the session
            return redirect('check_otp', username=username)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forget_password')
    return render(request, 'send_otp.html')

@csrf_exempt
def check_otp(request, username):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            user = User.objects.get(username=username)
            # Assuming you have stored the OTP in session or database
            # Here, I'm assuming it's stored in session
            stored_otp = request.session.get('otp')
            if stored_otp == otp:
                return redirect('reset_password', username=username)
            else:
                messages.error(request, 'Invalid OTP.')
                return redirect('send_otp')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forget_password')
    return render(request, 'otp.html', {'username': username})


@csrf_exempt
def security_questions(request):
    if request.method == 'POST':
        # Get username from session that was stored during signup
        username = request.session.get('signup_username')
        if not username:
            messages.error(request, 'Session expired. Please sign up again.')
            return redirect('sign_up')
            
        primary_school = request.POST.get('primary_school')
        favorite_color = request.POST.get('favorite_color')
        pet_name = request.POST.get('pet_name')
        
        # Create new security questions entry
        SecurityQuestion.objects.create(
            username=username,
            primary_school=primary_school,
            favorite_color=favorite_color,
            pet_name=pet_name
        )
        
        # Clear the session variable after using it
        del request.session['signup_username']
        
        messages.success(request, 'Security questions saved successfully.')
        return redirect('log_in')  # Redirect to login page
        
    return render(request, 'question.html')



@csrf_exempt
def reset_password(request, username):
    try:
        user = User.objects.get(username=username)
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return redirect('reset_password', username=username)
                
            # Set the new password
            user.set_password(new_password)
            user.save()
            
            messages.success(request, 'Password reset successfully. Please login with your new password.')
            return redirect('log_in')
            
        return render(request, 're_set.html')
        
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('forget_password')

