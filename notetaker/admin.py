from django.contrib import admin
from .models import Campaign, Session, Recording, Transcription, Summary, CustomVocabulary

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'description')
    search_fields = ('name',)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'campaign', 'date_played')
    list_filter = ('campaign', 'date_played')
    search_fields = ('title', 'description')

@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'duration_seconds', 'uploaded_at')
    list_filter = ('session__campaign',)

@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'recording', 'assembly_id', 'processed_at')
    search_fields = ('assembly_id', 'raw_text')

@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'transcription', 'summary_type', 'model_used', 'created_at')
    list_filter = ('summary_type', 'model_used')

@admin.register(CustomVocabulary)
class CustomVocabularyAdmin(admin.ModelAdmin):
    list_display = ('term', 'campaign', 'note')
    list_filter = ('campaign', 'note')
    search_fields = ('term',)