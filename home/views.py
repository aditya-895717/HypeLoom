from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
import json
import secrets
from datetime import timedelta
from .forms import RegisterForm, SigninForm
from .models import CustomUser, UserProfile, LoginHistory, PasswordResetToken


# ==================== INDEX VIEW ====================

def index(request):
    """Home page view"""
    context = {
        'page_title': 'Home',
    }
    return render(request, 'index.html', context)


# ==================== REGISTRATION VIEW ====================

@require_http_methods(["GET", "POST"])
@csrf_protect
def register(request):
    """
    Handle user registration (GET and POST)
    Supports both regular form submission and AJAX requests
    """
    
    # Redirect if already authenticated
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            try:
                data = json.loads(request.body)
                form = RegisterForm(data)
                
                if form.is_valid():
                    user = form.save()
                    
                    # Create user profile
                    UserProfile.objects.create(user=user)
                    
                    # Log the user in
                    login(request, user)
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Account created successfully! Redirecting...',
                        'redirect': reverse_lazy('dashboard'),
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'full_name': user.full_name,
                        }
                    }, status=201)
                
                else:
                    # Format form errors
                    errors = {}
                    for field, field_errors in form.errors.items():
                        errors[field] = [str(error) for error in field_errors]
                    
                    return JsonResponse({
                        'success': False,
                        'message': 'Registration failed. Please check the errors.',
                        'errors': errors
                    }, status=400)
            
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
            
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': 'An unexpected error occurred. Please try again.'
                }, status=500)
        
        else:
            # Regular form submission
            form = RegisterForm(request.POST)
            
            if form.is_valid():
                user = form.save()
                
                # Create user profile
                UserProfile.objects.create(user=user)
                
                # Log the user in
                login(request, user)
                
                # Redirect to dashboard
                return redirect('dashboard')
    
    else:
        form = RegisterForm()
    
    context = {
        'form': form,
        'page_title': 'Register',
    }
    return render(request, 'register.html', context)


# ==================== SIGN IN VIEW ====================

@require_http_methods(["GET", "POST"])
@csrf_protect
def signin(request):
    """
    Handle user sign in (GET and POST)
    Supports both regular form submission and AJAX requests
    Tracks login history for security
    """
    
    # Redirect if already authenticated
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            try:
                data = json.loads(request.body)
                form = SigninForm(data)
                
                if form.is_valid():
                    user = form.get_user()
                    
                    # Log the user in
                    login(request, user)
                    
                    # Update last login timestamp
                    user.last_login = timezone.now()
                    user.save(update_fields=['last_login'])
                    
                    # Record login history
                    try:
                        LoginHistory.objects.create(
                            user=user,
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            device_type=get_device_type(request),
                        )
                    except Exception as e:
                        print(f"Error recording login history: {e}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Signed in successfully!',
                        'redirect': reverse_lazy('dashboard'),
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'full_name': user.full_name,
                        }
                    }, status=200)
                
                else:
                    # Format form errors
                    errors = {}
                    for field, field_errors in form.errors.items():
                        errors[field] = [str(error) for error in field_errors]
                    
                    return JsonResponse({
                        'success': False,
                        'message': 'Sign in failed. Please check your credentials.',
                        'errors': errors
                    }, status=401)
            
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
            
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': 'An unexpected error occurred. Please try again.'
                }, status=500)
        
        else:
            # Regular form submission
            form = SigninForm(request.POST)
            
            if form.is_valid():
                user = form.get_user()
                
                # Log the user in
                login(request, user)
                
                # Update last login
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                
                # Record login history
                try:
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        device_type=get_device_type(request),
                    )
                except Exception as e:
                    print(f"Error recording login history: {e}")
                
                # Redirect to dashboard
                return redirect('dashboard')
    
    else:
        form = SigninForm()
    
    context = {
        'form': form,
        'page_title': 'Sign In',
    }
    return render(request, 'signin.html', context)


# ==================== LOGOUT VIEW ====================

@require_POST
def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('signin')


# ==================== DASHBOARD VIEW ====================

@login_required(login_url='signin')
def dashboard(request):
    """User dashboard - requires login"""
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    # Get recent login history
    recent_logins = LoginHistory.objects.filter(user=user).order_by('-login_at')[:5]
    
    context = {
        'user': user,
        'profile': profile,
        'recent_logins': recent_logins,
        'page_title': 'Dashboard',
    }
    return render(request, 'dashboard.html', context)


# ==================== PROFILE VIEW ====================

@login_required(login_url='signin')
def profile(request):
    """User profile page - requires login"""
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    if request.method == 'POST':
        # Update profile
        user.full_name = request.POST.get('full_name', user.full_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.street_address = request.POST.get('street_address', user.street_address)
        user.city = request.POST.get('city', user.city)
        user.state = request.POST.get('state', user.state)
        user.postal_code = request.POST.get('postal_code', user.postal_code)
        user.country = request.POST.get('country', user.country)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        # Update profile preferences
        profile.preferred_size_women = request.POST.get('preferred_size_women', profile.preferred_size_women)
        profile.preferred_size_men = request.POST.get('preferred_size_men', profile.preferred_size_men)
        profile.shoe_size = request.POST.get('shoe_size', profile.shoe_size)
        profile.save()
        
        return redirect('profile')
    
    context = {
        'user': user,
        'profile': profile,
        'page_title': 'Profile',
    }
    return render(request, 'profile.html', context)


# ==================== HELPER FUNCTIONS ====================

def get_client_ip(request):
    """
    Get client IP address from request
    Handles X-Forwarded-For header for proxied requests
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_type(request):
    """
    Determine device type from user agent
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if 'mobile' in user_agent or 'android' in user_agent:
        return 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'tablet'
    else:
        return 'desktop'


def send_verification_email(user):
    """
    Send email verification link to user
    """
    token = secrets.token_urlsafe(32)
    
    PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=24)
    )
    
    verification_url = f"{settings.SITE_URL}/verify-email/{token}/"
    
    subject = 'Verify Your HYPELOOM Account'
    message = f"""
    Hello {user.full_name},
    
    Thank you for creating an account with HYPELOOM!
    
    Please verify your email address by clicking the link below:
    {verification_url}
    
    This link will expire in 24 hours.
    
    Best regards,
    The HYPELOOM Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_password_reset_email(user):
    """
    Send password reset link to user
    """
    token = secrets.token_urlsafe(32)
    
    PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=1)
    )
    
    reset_url = f"{settings.SITE_URL}/reset-password/{token}/"
    
    subject = 'Reset Your HYPELOOM Password'
    message = f"""
    Hello {user.full_name},
    
    We received a request to reset your password.
    
    Click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request this, you can ignore this email.
    
    Best regards,
    The HYPELOOM Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# ==================== API ENDPOINTS ====================

@login_required
@require_http_methods(["GET"])
def check_email_exists(request):
    """
    AJAX endpoint to check if email is already registered
    """
    email = request.GET.get('email', '').lower().strip()
    
    if not email:
        return JsonResponse({'exists': False})
    
    exists = CustomUser.objects.filter(email=email).exists()
    
    return JsonResponse({'exists': exists})


@login_required
@require_http_methods(["POST"])
@csrf_protect
def update_profile(request):
    """
    AJAX endpoint to update user profile
    """
    try:
        data = json.loads(request.body)
        user = request.user
        profile = UserProfile.objects.get(user=user)
        
        # Update user fields
        user.full_name = data.get('full_name', user.full_name)
        user.phone_number = data.get('phone_number', user.phone_number)
        user.city = data.get('city', user.city)
        user.state = data.get('state', user.state)
        user.postal_code = data.get('postal_code', user.postal_code)
        user.country = data.get('country', user.country)
        user.save()
        
        # Update profile preferences
        profile.preferred_size_women = data.get('preferred_size_women', profile.preferred_size_women)
        profile.preferred_size_men = data.get('preferred_size_men', profile.preferred_size_men)
        profile.shoe_size = data.get('shoe_size', profile.shoe_size)
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully!'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)