from django import forms

from django.contrib.auth import views as auth_views

# urlpatterns = [
#     path('', profile_views.home, name='profile-home'),
#     path('signin', profile_views.signin, name='signin'),
#     path('login', auth_views.LoginView.as_view(
#         template_name='profiles/signin.html'), name='login'),


class SigninForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Password', 'type': 'password'}))
