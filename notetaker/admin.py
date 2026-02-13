from django.contrib import admin
from .models import Campaign, Session, Recording, Transcription, Summary, CustomVocabulary, Subscription

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

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    # What shows up in the main list view of all subscriptions
    list_select_related = ['user']
    list_display = (
        'user', 
        'status', 
        'plan_tier', 
        'monthly_audio_minutes_used', 
        'summaries_generated_count', 
        'is_active_status'

    )
    list_filter = ('status', 'plan_tier')
    search_fields = ('user__username', 'user__email')
    
    # Organizes the detail view into clean, collapsible sections
    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Payment & Tier Status', {
            'fields': (
                'status', 
                'plan_tier'
            )
        }),
        ('Usage Quotas', {
            'fields': (
                'monthly_audio_minutes_used', 
                'audio_minutes_limit', 
                'summaries_generated_count'
            )
        }),
        ('Lifecycle & Billing Dates', {
            'fields': (
                'billing_cycle_anchor', 
                'current_period_start', 
                'current_period_end', 
                'cancel_at_period_end'
            )
        })
        # ('App Features & Limits', {
        #     'fields': (
        #         'has_custom_vocabulary_access', 
        #         'max_campaigns_allowed'
        #     )
        # }),
        # ('System Timestamps', {
        #     'fields': ('created_at', 'updated_at'),
        #     'classes': ('collapse',) # Hides this section by default
        # }),
    )

    @admin.display(boolean=True, description='Is Active')
    def is_active_status(self, obj):
        """
        Wrapper for the model's is_active property. 
        The @admin.display(boolean=True) decorator tells Django to render this 
        as a nice green checkmark or red X in the list view.
        """
        return obj.is_active