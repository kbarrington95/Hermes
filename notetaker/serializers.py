from rest_framework import serializers
from .models import Campaign, Session, Recording, Transcription, Summary, CustomVocabulary

class CustomVocabularySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomVocabulary
        fields = ['id', 'term', 'note']

class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ['id', 'model_used', 'content', 'summary_type', 'created_at']

class TranscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcription
        fields = ['id', 'assembly_id', 'raw_text', 'utterances_json', 'processed_at']

class RecordingSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.SerializerMethodField(method_name='get_duration_minutes')

    class Meta:
        model = Recording
        fields = ['id', 'audio_file', 'duration_seconds', 'duration_minutes', 'uploaded_at', 'transcription']

    def get_duration_minutes(self, recording: Recording):
        if recording.duration_seconds:
            return round(recording.duration_seconds / 60, 2)
        return 0

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

    