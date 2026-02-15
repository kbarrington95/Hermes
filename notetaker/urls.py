from django.urls import path
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

sessions_router = routers.NestedDefaultRouter(router, 'sessions', lookup='session')
sessions_router.register('recording', views.RecordingViewSet, basename='session-recording')

# Define the URL patterns
urlpatterns = router.urls + sessions_router.urls