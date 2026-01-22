from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    
    # User dashboard and profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # API endpoints
    path('api/check-email/', views.check_email_exists, name='check_email'),
    path('api/update-profile/', views.update_profile, name='update_profile'),]