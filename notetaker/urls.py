from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

# Create the router and register our viewsets
router = DefaultRouter()

# The first argument is the URL prefix (e.g., 'campaigns' -> /campaigns/)
router.register('campaigns', views.CampaignViewSet)
router.register('sessions', views.SessionViewSet)
router.register('recordings', views.RecordingViewSet)
router.register('transcriptions', views.TranscriptionViewSet)
router.register('summaries', views.SummaryViewSet)
router.register('vocabulary', views.CustomVocabularyViewSet)

# Define the URL patterns
urlpatterns = router.urls