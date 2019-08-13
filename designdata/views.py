from django.shortcuts import render
from django import forms
from django.contrib.auth.decorators import login_required


@login_required(login_url='signin')
def home(request):
    context = {
        "name": request.user.get_full_name(),
        "title1": "Hydro Dash",
        "activename": "CFD Results",
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
