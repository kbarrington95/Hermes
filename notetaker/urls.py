from django.urls import path
from . import views


# URLConf
urlpatterns = [
    path('campaigns/', views.CampaignList.as_view()),
    path('campaigns/<int:id>', views.campaign_detail),
]
