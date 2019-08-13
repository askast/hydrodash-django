from django.urls import path
from . import views as profile_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', profile_views.home, name='profile-home'),
    path('signin', profile_views.SigninView.as_view(
        template_name='profiles/signin.html'), name='signin'),
    path('signout', auth_views.LogoutView.as_view(
        template_name='profiles/signout.html'), name='signout'),
]
