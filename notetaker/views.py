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
from .services import AssemblyAIService, GeminiService
from .tasks import process_transcription
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
        """
        Triggers a background Celery task to transcribe a specific recording.
        URL: POST /api/recordings/<id>/transcribe/
        """
        recording = self.get_object()

        # 1. Protect your API credits using your OneToOne related_name
        if hasattr(recording, 'transcription'):
            return Response(
                {"message": "This recording has already been transcribed."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Trigger the background task, passing ONLY the ID
        process_transcription.delay(recording.id)  # type: ignore

        # 3. Immediately respond so the user isn't kept waiting
        return Response(
            {"message": "Transcription sent to background worker. Check back soon!"},
            status=status.HTTP_202_ACCEPTED
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
    
    @action(detail=True, methods=['POST','GET'])
    def summarize(self, request, pk=None):
        """
        Manual trigger to generate a D&D session summary using Gemini.
        URL: POST /api/transcriptions/<id>/summarize/
        """
        # 1. Get the transcription object
        transcription = self.get_object() 

        # 2. Check if a summary already exists to save API credits
        existing_summary = Summary.objects.filter(transcription=transcription).first()
        if existing_summary:
             serializer = SummarySerializer(existing_summary)
             return Response(
                 {"message": "Already summarized", "data": serializer.data},
                 status=status.HTTP_200_OK
             )

        try:
            # 3. Call the Gemini Service using the raw text from the DB
            summary_text = GeminiService.generate_dnd_summary(transcription.raw_text)
            
            # 4. Save the generated summary to the Database
            summary = Summary.objects.create(
                transcription=transcription,
                model_used='gemini-2.5-flash',
                summary_type='dnd_session',  # Update this if your model expects a different default
                content=summary_text
            )

            # 5. Return the serialized result
            return Response(
                SummarySerializer(summary).data, 
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        
