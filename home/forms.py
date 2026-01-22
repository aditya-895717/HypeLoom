from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import re
from .models import CustomUser


class RegisterForm(forms.ModelForm):
    """
    User registration form with validation
    Includes password confirmation and strength validation
    """
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter a strong password',
            'minlength': '8',
            'required': True
        }),
        help_text='At least 8 characters with uppercase, lowercase, and numbers'
    )
    
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirm your password',
            'required': True
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('full_name', 'email')
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'John Doe',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'you@example.com',
                'required': True
            }),
        }
    
    def clean_full_name(self):
        """Validate full name format and length"""
        full_name = self.cleaned_data.get('full_name', '').strip()
        
        if len(full_name) < 2:
            raise ValidationError('Name must be at least 2 characters long.')
        
        if len(full_name) > 120:
            raise ValidationError('Name must be less than 120 characters.')
        
        if not re.match(r"^[a-zA-Z\s\'-]+$", full_name):
            raise ValidationError(
                'Name can only contain letters, spaces, hyphens, and apostrophes.'
            )
        
        return full_name
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(
                'This email is already registered. Please sign in instead.'
            )
        
        return email
    
    def clean_password(self):
        """Validate password strength"""
        password = self.cleaned_data.get('password', '')
        
        # Check length
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        # Check for digit
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one digit.')
        
        # Check for common weak passwords
        weak_passwords = ['password', 'password123', '12345678', 'qwerty123']
        if password.lower() in weak_passwords:
            raise ValidationError('This password is too common. Please choose a stronger password.')
        
        return password
    
    def clean(self):
        """Validate password confirmation"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save user with hashed password"""
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email'].lower().strip()
        user.full_name = self.cleaned_data['full_name'].strip()
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
        
        return user


class SigninForm(forms.Form):
    """
    User sign in form with authentication
    """
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
            'required': True
        })
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'required': True
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean(self):
        """Authenticate user credentials"""
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').lower().strip()
        password = cleaned_data.get('password')
        
        if email and password:
            try:
                # Get user by email
                user = CustomUser.objects.get(email=email)
                
                # Check password
                if not user.check_password(password):
                    raise ValidationError('Invalid email or password.')
                
                # Check if account is active
                if not user.is_active:
                    raise ValidationError('This account has been deactivated.')
                
                # Store user for later retrieval
                self.user = user
            
            except CustomUser.DoesNotExist:
                raise ValidationError('Invalid email or password.')
        
        return cleaned_data
    
    def get_user(self):
        """Return authenticated user"""
        return getattr(self, 'user', None)


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information
    """
    
    class Meta:
        model = CustomUser
        fields = [
            'full_name',
            'phone_number',
            'profile_picture',
            'date_of_birth',
            'gender',
            'street_address',
            'city',
            'state',
            'postal_code',
            'country',
            'bio'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class PasswordChangeForm(forms.Form):
    """
    Form for changing password
    """
    
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='At least 8 characters with uppercase, lowercase, and numbers'
    )
    
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def clean_current_password(self):
        """Verify current password"""
        current_password = self.cleaned_data.get('current_password')
        
        if not self.user.check_password(current_password):
            raise ValidationError('Current password is incorrect.')
        
        return current_password
    
    def clean_new_password(self):
        """Validate new password strength"""
        new_password = self.cleaned_data.get('new_password', '')
        
        if len(new_password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        if not re.search(r'[A-Z]', new_password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        if not re.search(r'[a-z]', new_password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        if not re.search(r'\d', new_password):
            raise ValidationError('Password must contain at least one digit.')
        
        return new_password
    
    def clean(self):
        """Validate password confirmation"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError('New passwords do not match.')
        
        return cleaned_data
    
    def save(self):
        """Save new password"""
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user