from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.aggregates import Count
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet

from .models import (
    Campaign, 
    Session, 
    Recording, 
    Transcription, 
    Summary, 
    CustomVocabulary
)
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'sessions_count']

    def get_serializer_context(self):
        return {'request': self.request}


class SessionViewSet(ModelViewSet):
    queryset = Session.objects.annotate(recordings_count=Count('recordings')) \
                              .select_related('campaign').all()
    serializer_class = SessionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['campaign_id']
    search_fields = ['title', 'description']
    ordering_fields = ['date_played', 'created_at', 'recordings_count']

    def get_serializer_context(self):
        return {'request': self.request}


class RecordingViewSet(ModelViewSet):
    queryset = Recording.objects.select_related('session').all()
    serializer_class = RecordingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['session_id']
    search_fields = ['audio_file']
    ordering_fields = ['uploaded_at', 'duration_seconds']

    def get_serializer_context(self):
        return {'request': self.request}


class TranscriptionViewSet(ModelViewSet):
    queryset = Transcription.objects.select_related('recording').all()
    serializer_class = TranscriptionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['recording_id']
    search_fields = ['raw_text', 'assembly_id']
    ordering_fields = ['processed_at']

    def get_serializer_context(self):
        return {'request': self.request}


class SummaryViewSet(ModelViewSet):
    queryset = Summary.objects.select_related(
        'transcription__recording__session__campaign'
    ).all()
    serializer_class = SummarySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transcription_id', 'summary_type', 'model_used']
    search_fields = ['content']
    ordering_fields = ['created_at']
    
    def get_serializer_context(self):
        return {'request': self.request}


class CustomVocabularyViewSet(ModelViewSet):
    queryset = CustomVocabulary.objects.select_related('campaign').all()
    serializer_class = CustomVocabularySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['campaign_id']
    search_fields = ['term', 'note']
    ordering_fields = ['term']

    def get_serializer_context(self):
        return {'request': self.request}