from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import format_html
import markdown
from .models import Campaign, Session, Recording, Transcription, Summary, CustomVocabulary, Subscription

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'description')
    search_fields = ('name',)

class RecordingInline(admin.TabularInline):
    model = Recording
    extra = 0
    fields = ('audio_file', 'uploaded_at')
    readonly_fields = ('audio_file', 'uploaded_at')

class TranscriptionInline(admin.StackedInline):
    model = Transcription
    extra = 0
    fields = ('status', 'assembly_id', 'processing_duration', 'raw_text')
    readonly_fields = ('raw_text', 'processing_duration')

class SummaryInline(admin.StackedInline):
    model = Summary
    extra = 0
    fields = ('id', 'summary_type', 'model_used', 'content')
    readonly_fields = ('content',) 

# notetaker/admin.py

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'campaign', 'date_played', 'has_summary')
    list_filter = ('campaign', 'date_played')
    search_fields = ('title', 'description')
    
    # 1. Add RecordingInline so you can manage the file here
    inlines = [RecordingInline]

    # 2. Add these methods to readonly_fields to display them on the page
    readonly_fields = ('display_transcription', 'display_summary')

    def has_summary(self, obj):
        """
        Checks if at least one summary exists for this session's recording.
        """
        try:
            # We follow the chain to the transcription
            # Then check if the 'summaries' set has any records
            return obj.recording.transcription.summaries.exists()
        except (AttributeError, Recording.DoesNotExist, Transcription.DoesNotExist):
            # Returns False if any part of the chain (Recording or Transcription) is missing
            return False
            
    has_summary.boolean = True
    has_summary.short_description = 'Summarized?'

    def display_transcription(self, obj):
        try:
            # Follow the chain: Session -> Recording -> Transcription
            transcription_id = obj.recording.transcription.id
            
            # Generate the URL for the Transcription "Change" page in Admin
            url = reverse('admin:notetaker_transcription_change', args=[transcription_id])
            
            return format_html('<a href="{}">View Full Session Transcription</a>', url)
        except (AttributeError, Recording.DoesNotExist, Transcription.DoesNotExist):
            return "No transcription available yet."
    
    display_transcription.short_description = "Transcription"

    def display_summary(self, obj):
        try:
            # 1. Access the OneToOne recording
            recording = obj.recording 
            # 2. Access the OneToOne transcription
            transcription = recording.transcription 
            # 3. Access the first summary from the 'summaries' related_name
            # NOTE: Because it's a ForeignKey, it's transcription.summaries, not transcription.summary
            summary = transcription.summaries.first() 

            if summary and summary.content:
                html = markdown.markdown(summary.content)
                return mark_safe(html)
            
            return "Summary pending or not yet generated."
        except (AttributeError, Recording.DoesNotExist, Transcription.DoesNotExist):
            return "Chain incomplete (No recording or transcription yet)."
    
    display_summary.short_description = "Gemini Summary"


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'duration_seconds', 'uploaded_at')
    list_filter = ('session__campaign',)
    inlines = [TranscriptionInline]

@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'recording', 'assembly_id', 'submitted_at')
    search_fields = ('assembly_id', 'raw_text')
    inlines = [SummaryInline]
    

@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'transcription', 'summary_type', 'model_used', 'created_at')
    list_filter = ('summary_type', 'model_used')
    readonly_fields = ('formatted_content',)


    def formatted_content(self, obj):
        """
        Converts the raw markdown text into HTML and tells Django it is safe to render.
        """
        if obj.content:
            # 1. Convert Markdown to HTML
            html_content = markdown.markdown(obj.content)
            # 2. Tell Django this HTML is safe to display
            return mark_safe(html_content)
        return "No summary generated yet."
    
    # This sets the label for the field in the admin interface
    formatted_content.short_description = 'Rendered D&D Notes' #type:ignore

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