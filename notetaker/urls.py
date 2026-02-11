from django.urls import path
from . import views


# URLConf
urlpatterns = [
    path('campaigns/', views.campaign_list)
]
