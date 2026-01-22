from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator, MinLengthValidator, RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import re


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser
    Provides additional fields for fashion e-commerce platform
    """
    
    # Basic Information
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="User's email address"
    )
    full_name = models.CharField(
        max_length=120,
        help_text="User's full name"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='Phone number must contain between 9 and 15 digits.',
            code='invalid_phone'
        )],
        help_text="User's phone number"
    )
    
    # Profile Information
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        help_text="User's profile picture"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="User's biography"
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="User's date of birth"
    )
    
    # Address Information
    street_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Street address"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="City"
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="State or province"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Postal code"
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Country"
    )
    
    # Gender and Preferences
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        help_text="User's gender"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Account creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    last_login = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last login timestamp"
    )
    
    # Status and Preferences
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the user account is active"
    )
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Whether the email has been verified"
    )
    email_verified_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Email verification timestamp"
    )
    
    newsletter_subscription = models.BooleanField(
        default=True,
        help_text="Whether the user is subscribed to newsletter"
    )
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User's notification preferences"
    )
    
    # Configure the authentication field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'username']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def get_full_address(self):
        """Get user's complete address"""
        parts = [
            self.street_address,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in parts if part])
    
    def clean(self):
        """Validate user data"""
        super().clean()
        
        # Validate full name
        if self.full_name:
            if len(self.full_name) < 2:
                raise ValidationError({'full_name': 'Name must be at least 2 characters long.'})
            
            if not re.match(r"^[a-zA-Z\s\'-]+$", self.full_name):
                raise ValidationError({'full_name': 'Name can only contain letters, spaces, hyphens, and apostrophes.'})
    
    def save(self, *args, **kwargs):
        """Save user with validation"""
        self.clean()
        self.full_name = self.full_name.strip() if self.full_name else ''
        self.email = self.email.lower().strip()
        
        if not self.username:
            self.username = self.email
        
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """
    Extended user profile for additional commerce-related data
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Preferences
    preferred_size_women = models.CharField(
        max_length=10,
        blank=True,
        choices=[
            ('XS', 'Extra Small'),
            ('S', 'Small'),
            ('M', 'Medium'),
            ('L', 'Large'),
            ('XL', 'Extra Large'),
            ('2XL', '2XL'),
            ('3XL', '3XL'),
        ]
    )
    preferred_size_men = models.CharField(
        max_length=10,
        blank=True,
        choices=[
            ('XS', 'Extra Small'),
            ('S', 'Small'),
            ('M', 'Medium'),
            ('L', 'Large'),
            ('XL', 'Extra Large'),
            ('2XL', '2XL'),
            ('3XL', '3XL'),
        ]
    )
    
    shoe_size = models.CharField(
        max_length=10,
        blank=True,
        help_text="Shoe size"
    )
    
    # Loyalty Program
    loyalty_points = models.IntegerField(
        default=0,
        help_text="Accumulated loyalty points"
    )
    total_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total amount spent"
    )
    
    # Preferences
    favorite_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Favorite product categories"
    )
    price_range_preference = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('budget', 'Budget (Under $50)'),
            ('mid', 'Mid-range ($50-$150)'),
            ('premium', 'Premium ($150-$500)'),
            ('luxury', 'Luxury ($500+)'),
        ]
    )
    
    # Shopping Behavior
    orders_count = models.IntegerField(
        default=0,
        help_text="Total number of orders"
    )
    average_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Average order value"
    )
    last_purchase_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date of last purchase"
    )
    
    # Account Status
    is_vip = models.BooleanField(
        default=False,
        help_text="VIP customer status"
    )
    vip_tier = models.CharField(
        max_length=20,
        choices=[
            ('silver', 'Silver'),
            ('gold', 'Gold'),
            ('platinum', 'Platinum'),
            ('diamond', 'Diamond'),
        ],
        blank=True,
        help_text="VIP tier level"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Profile of {self.user.full_name}"
    
    def get_vip_benefits(self):
        """Get benefits based on VIP tier"""
        benefits = {
            'silver': {
                'discount': 5,
                'free_shipping_threshold': 75,
                'returns_days': 30,
                'priority_support': False,
            },
            'gold': {
                'discount': 10,
                'free_shipping_threshold': 50,
                'returns_days': 45,
                'priority_support': True,
            },
            'platinum': {
                'discount': 15,
                'free_shipping_threshold': 0,
                'returns_days': 60,
                'priority_support': True,
            },
            'diamond': {
                'discount': 20,
                'free_shipping_threshold': 0,
                'returns_days': 90,
                'priority_support': True,
            },
        }
        return benefits.get(self.vip_tier, {})


class LoginHistory(models.Model):
    """
    Track user login history for security and analytics
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address of login"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    device_type = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('desktop', 'Desktop'),
            ('tablet', 'Tablet'),
            ('mobile', 'Mobile'),
        ]
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Approximate location"
    )
    login_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Login timestamp"
    )
    is_suspicious = models.BooleanField(
        default=False,
        help_text="Whether login appears suspicious"
    )
    
    class Meta:
        verbose_name = 'Login History'
        verbose_name_plural = 'Login Histories'
        ordering = ['-login_at']
        indexes = [
            models.Index(fields=['user', '-login_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.login_at.strftime('%Y-%m-%d %H:%M:%S')}"


class PasswordResetToken(models.Model):
    """
    Manage password reset tokens
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Reset token"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Token creation time"
    )
    expires_at = models.DateTimeField(
        help_text="Token expiration time"
    )
    used = models.BooleanField(
        default=False,
        help_text="Whether token has been used"
    )
    used_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When token was used"
    )
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']
    
    def is_valid(self):
        """Check if token is still valid"""
        return not self.used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Reset token for {self.user.email}"