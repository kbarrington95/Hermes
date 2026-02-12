from django.shortcuts import get_object_or_404
from django.db.models.aggregates import Count
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from .models import Campaign, Session, Recording, Transcription, Summary, CustomVocabulary
from .serializers import (
    CampaignSerializer, 
    SessionSerializer, 
    RecordingSerializer, 
    TranscriptionSerializer, 
    SummarySerializer, 
    CustomVocabularySerializer
)

class CampaignViewSet(ModelViewSet):
    queryset = Campaign.objects.annotate(sessions_count=Count('sessions')).all()
    serializer_class = CampaignSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    # Note: We are using standard Cascade deletion here (from models.py).
    # If you delete a Campaign, all Sessions/Recordings are deleted automatically.
    # Unlike your Store app, we likely don't need to block deletion here.

class SessionViewSet(ModelViewSet):
    # Annotate recordings_count and optimize campaign fetch
    queryset = Session.objects.annotate(recordings_count=Count('recordings')).select_related('campaign').all()
    serializer_class = SessionSerializer

    def get_serializer_context(self):
        return {'request': self.request}

class RecordingViewSet(ModelViewSet):
    # Optimize session fetch
    queryset = Recording.objects.select_related('session').all()
    serializer_class = RecordingSerializer

    def get_serializer_context(self):
        return {'request': self.request}

class TranscriptionViewSet(ModelViewSet):
    # Optimize recording fetch
    queryset = Transcription.objects.select_related('recording').all()
    serializer_class = TranscriptionSerializer

    def get_serializer_context(self):
        return {'request': self.request}

class SummaryViewSet(ModelViewSet):
    # Fetch transcription, recording, session, and campaign in one single efficient query
    queryset = Summary.objects.select_related(
        'transcription__recording__session__campaign'
    ).all()
    serializer_class = SummarySerializer
    
    def get_serializer_context(self):
        return {'request': self.request}

class CustomVocabularyViewSet(ModelViewSet):
    queryset = CustomVocabulary.objects.select_related('campaign').all()
    serializer_class = CustomVocabularySerializer

    def get_serializer_context(self):
        return {'request': self.request}