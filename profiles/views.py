from django.shortcuts import render
from django import forms
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView


@login_required(login_url='signin')
def home(request):
    context = {
        "name": request.user.get_full_name(),
        "title1": "Hydro Dash",
        "activename": "Test List",
        "dropdowndata": [{
            "name": "Print",
            "url": "#"
        }, {
            "name": "Generate Report",
            "url": "#"
        }, {
            "name": "dropdown3",
            "url": "#"
        }, ]
    }
    return render(request, 'profiles/home.html', context)


class SigninView(auth_views.LoginView):
    remember = forms.CheckboxInput()
