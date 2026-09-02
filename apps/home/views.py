# apps/home/views.py

from django.shortcuts import render

from .context import HomeContextBuilder


def home(request):
    context = HomeContextBuilder.build(request)
    return render(request, "home/home.html", context)
