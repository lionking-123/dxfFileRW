# -*- coding: utf-8 -*-
from django.views.generic import ListView, DetailView 
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponse
from django.urls import reverse_lazy

from django.shortcuts import render
from django.http import JsonResponse
from .dxfapi import getJsonData

def home(request):

    return render(request, 'products/index.html', {'foo': 'bar', })

def getdxf(request):
    id = request.GET.get('url')
    res = getJsonData(id)
    return HttpResponse(res, content_type="application/json")
    