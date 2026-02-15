from rest_framework import serializers
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

class SessionSerializer(serializers.ModelSerializer):
    recordings_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Session
        fields = ['id', 'title', 'date_played', 'description', 'created_at', 'recordings_count']

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