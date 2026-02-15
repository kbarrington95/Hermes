from rest_framework import serializers
from django.utils import timezone
from .models import Campaign, Session, Recording, Transcription, Summary, CustomVocabulary, Subscription

class CustomVocabularySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomVocabulary
        fields = ['id', 'term', 'note']

class SummarySerializer(serializers.ModelSerializer):
    # Walk up the tree to get parent IDs
    recording = serializers.IntegerField(source='transcription.recording.id', read_only=True)
    session = serializers.IntegerField(source='transcription.recording.session.id', read_only=True)
    campaign = serializers.IntegerField(source='transcription.recording.session.campaign.id', read_only=True)

    class Meta:
        model = Summary
        # Add the new fields to the list
        fields = ['id', 'model_used', 'content', 'summary_type', 'created_at', 'transcription', 'recording', 'session', 'campaign']

class TranscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcription
        fields = ['id', 'assembly_id', 'raw_text', 'utterances_json', 'processed_at']

class RecordingSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.SerializerMethodField(method_name='get_duration_minutes')
    uploaded_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Recording
        fields = ['id', 'audio_file', 'duration_minutes', 'uploaded_at']

    def get_duration_minutes(self, recording: Recording):
        if recording.duration_seconds:
            return round(recording.duration_seconds / 60, 2)
        return 0
    
    def create(self, validated_data):
        session_id = self.context['session_id']
        return Recording.objects.create(session_id=session_id, **validated_data)
    
class UploadRecordingSerializer(serializers.ModelSerializer):
    # Input fields that don't exist directly on the Recording model
    campaign_id = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.all(), 
        source='session.campaign', # purely for documentation/schema generation
        write_only=True
    )
    date = serializers.DateField(required=False, write_only=True)
    title = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = Recording
        fields = ['id', 'audio_file', 'campaign_id', 'date', 'title', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def create(self, validated_data):
        campaign = validated_data.pop('session')['campaign'] # Extracted from source mapping
        date_played = validated_data.pop('date', timezone.now().date())
        
        # Default title logic: "Session - YYYY-MM-DD"
        default_title = f"Session - {date_played}"
        title = validated_data.pop('title', default_title)
        audio_file = validated_data.pop('audio_file')

        # Create the Session first
        session = Session.objects.create(
            campaign=campaign,
            title=title,
            date_played=date_played,
            description="Auto-created via recording upload"
        )
        # Create the Recording linked to the new Session
        recording = Recording.objects.create(
            session=session,
            audio_file=audio_file,
            **validated_data # Catch any other fields like duration if passed
        )
        
        return recording

class SessionSerializer(serializers.ModelSerializer):
    recording = RecordingSerializer()

    class Meta:
        model = Session
        fields = ['id', 'title', 'date_played', 'description', 'created_at', 'recording']

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ['id', 'name', 'description', 'created_at', 'sessions_count', 'vocabulary']

    sessions_count = serializers.IntegerField(read_only=True)
    vocabulary = CustomVocabularySerializer(many=True, read_only=True)

class SubscriptionSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ['id', 
                  'user_id',
                  'status',
                  'plan_tier']