from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.aggregates import Count
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .permissions import IsAdminOrReadOnly
from .services import AssemblyAIService
from .models import (
    Campaign, 
    Session, 
    Recording, 
    Transcription, 
    Summary, 
    CustomVocabulary,
    Subscription
)
from .serializers import (
    CampaignSerializer, 
    SessionSerializer, 
    RecordingSerializer, 
    TranscriptionSerializer, 
    SummarySerializer, 
    CustomVocabularySerializer,
    SubscriptionSerializer,
    UploadRecordingSerializer
)

class CampaignViewSet(ModelViewSet):
    queryset = Campaign.objects.annotate(sessions_count=Count('sessions')).all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'sessions_count']

    def get_serializer_context(self):
        return {'request': self.request}


class SessionViewSet(ModelViewSet):
    queryset = Session.objects.select_related('campaign', 'recording').all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['campaign_id']
    search_fields = ['title', 'description']
    ordering_fields = ['date_played', 'created_at']

    def get_serializer_context(self):
        return {'request': self.request}


class RecordingViewSet(ModelViewSet):
    #queryset = Recording.objects.select_related('session').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ['uploaded_at', 'duration_seconds']

    def get_queryset(self): #type:ignore
        user = self.request.user

        if user.is_staff:
            return Recording.objects.select_related('session').all()
        
        subscription_id = Subscription.objects.only('id').get(user_id=user.id)
        return Recording.objects.filter(session__campaign__subscription=subscription_id)

    def get_serializer_class(self): #type:ignore
        if self.request.method == 'POST':
            return UploadRecordingSerializer
        return RecordingSerializer

    def get_serializer_context(self):
        return {'request': self.request}
    
    @action(detail=True, methods=['POST','GET'])
    def transcribe(self, request, pk=None):
        # 1. Get the object using the viewset's built-in security (get_queryset)
        recording = self.get_object() 

        # 2. Check if already transcribed to save credits
        if hasattr(recording, 'transcription'):
             serializer = TranscriptionSerializer(recording.transcription)
             return Response(
                 {"message": "Already transcribed", "data": serializer.data},
                 status=status.HTTP_200_OK
             )

        try:
            # 3. Call the Service (Blocking call)
            # Use .path to get the absolute filesystem path
            transcript_obj = AssemblyAIService.transcribe(recording.audio_file.path)
            
            # 4. Save to Database
            transcription = Transcription.objects.create(
                recording=recording,
                assembly_id=transcript_obj.id,
                raw_text=transcript_obj.text,
                utterances_json=transcript_obj.json_response.get('utterances', []),
                processed_at=timezone.now()
            )

            # 5. Return the result
            return Response(
                TranscriptionSerializer(transcription).data, 
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TranscriptionViewSet(ModelViewSet):
    queryset = Transcription.objects.select_related('recording').all()
    serializer_class = TranscriptionSerializer
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transcription_id', 'summary_type', 'model_used']
    search_fields = ['content']
    ordering_fields = ['created_at']
    
    def get_serializer_context(self):
        return {'request': self.request}


class CustomVocabularyViewSet(ModelViewSet):
    queryset = CustomVocabulary.objects.select_related('campaign').all()
    serializer_class = CustomVocabularySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['campaign_id']
    search_fields = ['term', 'note']
    ordering_fields = ['term']

    def get_serializer_context(self):
        return {'request': self.request}

class SubscriptionViewSet(ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        subscription= Subscription.objects.get(user_id=request.user.id)
        if request.method == 'GET':
            serializer = SubscriptionSerializer(subscription)
            return Response (serializer.data)
        elif request.method == 'PUT':
            serializer = SubscriptionSerializer(subscription, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
