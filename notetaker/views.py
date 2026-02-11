from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def campaign_list(request):
    return HttpResponse('ok')