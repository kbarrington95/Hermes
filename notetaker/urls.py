from django.urls import path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

# Create the router and register our viewsets
router = DefaultRouter()

# The first argument is the URL prefix (e.g., 'campaigns' -> /campaigns/)
router.register('campaigns', views.CampaignViewSet)
router.register('sessions', views.SessionViewSet, basename='sessions')
#router.register('recordings', views.RecordingViewSet)
router.register('transcriptions', views.TranscriptionViewSet)
router.register('summaries', views.SummaryViewSet)
router.register('vocabulary', views.CustomVocabularyViewSet)
router.register('subscription', views.SubscriptionViewSet)
router.register('recordings', views.RecordingViewSet, basename='recordings')
router.register('webhooks', views.WebhookViewSet, basename='webhooks')


# Define the URL patterns
urlpatterns = [
    path('dashboard/', TemplateView.as_view(template_name='notetaker/dashboard.html')),
    path('upload/', TemplateView.as_view(template_name='notetaker/upload.html')),
    path('campaign/<int:pk>/', TemplateView.as_view(template_name='notetaker/campaign_detail.html')),
    path('session/<int:pk>/', TemplateView.as_view(template_name='notetaker/session_detail.html')),
] + router.urls