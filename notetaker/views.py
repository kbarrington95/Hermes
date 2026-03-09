from django.shortcuts import get_object_or_404
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.aggregates import Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .permissions import IsAdminOrReadOnly
from .services import AssemblyAIService, GeminiService
from .tasks import process_transcription, process_summary
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

        # 2. CREATE THE PENDING RECORD FIRST
        # This acts as our "placeholder" while AssemblyAI works.
        # We don't have an assembly_id yet, so we leave it blank for now.
        Transcription.objects.create(
            recording=recording,
            status=Transcription.Status.PENDING
        )

        # 3. Trigger the background task, passing ONLY the ID
        process_transcription.delay(recording.id)  # type: ignore

        # 4. Immediately respond so the user isn't kept waiting
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
    ordering_fields = ['submitted_at']

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
        # (Assuming you have a related_name='summary' or similar on your model)
        existing_summary = Summary.objects.filter(transcription=transcription).first()
        if existing_summary:
            return Response(
                {"message": "This transcription has already been summarized."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Trigger the background task, passing ONLY the ID
        process_summary.delay(transcription.id)  # type: ignore

        # 4. Immediately respond
        return Response(
            {"message": "Summarization sent to background worker. Check back soon!"},
            status=status.HTTP_202_ACCEPTED
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
        
@method_decorator(csrf_exempt, name='dispatch')
class WebhookViewSet(GenericViewSet):
    """
    ViewSet to handle external incoming signals (Webhooks).
    URL: POST /api/webhooks/assemblyai/
    """
    queryset = Transcription.objects.all()
    permission_classes = [AllowAny] # Essential for external services

    @action(detail=False, methods=['POST'])
    def assemblyai(self, request):
        # 1. Extract the tracking data from AssemblyAI
        transcript_id = request.data.get('transcript_id')
        status_report = request.data.get('status')

        if status_report == 'completed':
            # 2. Find the record we created in our 'transcribe' action
            transcription = get_object_or_404(Transcription, assembly_id=transcript_id)
            
            # 3. Use the SDK to pull the finished text
            import assemblyai as aai
            aai.settings.api_key = settings.ASSEMBLY_AI_API_KEY
            transcript = aai.Transcript.get_by_id(transcript_id)

            # 4. Update the record with the final data
            if transcript.text:
                transcription.raw_text = transcript.text
            transcription.status = Transcription.Status.COMPLETED
            transcription.completed_at = timezone.now()
            
            # Calculate duration for your new DurationField
            start = transcription.submitted_at
            end = transcription.completed_at

            if start and end:
                full_duration = end - start
                # Create a clean duration by stripping microseconds
                transcription.processing_duration = timezone.timedelta(
                    seconds=int(full_duration.total_seconds())
                )
            
            transcription.save()

            # 5. AUTOMATION: Kick off the Gemini summary immediately
            process_summary.delay(transcription.id) # type: ignore

            return Response({"status": "success"}, status=status.HTTP_200_OK)

        elif status_report == 'error':
            # Handle potential failures gracefully
            Transcription.objects.filter(assembly_id=transcript_id).update(
                status=Transcription.Status.FAILED
            )

        return Response({"status": "received"}, status=status.HTTP_200_OK)