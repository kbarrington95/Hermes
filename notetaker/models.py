from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class Subscription(models.Model):

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAST_DUE = 'past_due', 'Past Due'
        CANCELED = 'canceled', 'Canceled'
        UNPAID = 'unpaid', 'Unpaid'
        TRIALING = 'trialing', 'Trialing'
        INACTIVE = 'inactive', 'Inactive' # Default for free/unsubscribed users

    class Tier(models.TextChoices):
        FREE = 'free', 'Free Tier'
        BASIC = 'basic', 'Basic Tier'
        PRO = 'pro', 'Pro Tier'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')

    # for payment processors?
    # customer_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    # subscription_id = models.CharField(max_length=100, blank=True, null=True, unique=True)

    # 2. Subscription Status & Tiers
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INACTIVE)
    plan_tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.FREE)

    # 3. Usage Quotas
    monthly_audio_minutes_used = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Minutes of transcription used this cycle."
    )
    audio_minutes_limit = models.IntegerField(
        default=60, 
        help_text="Max audio minutes allowed per billing cycle."
    )
    summaries_generated_count = models.IntegerField(
        default=0, 
        help_text="Number of summaries generated this cycle."
    )
    
    # 4. Lifecycle Dates
    billing_cycle_anchor = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="When the usage quotas should reset to zero."
    )
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(
        default=False, 
        help_text="True if user canceled but retains access until the period ends."
    )

    # 5. Feature Flags & App Limits
    # has_custom_vocabulary_access = models.BooleanField(default=False)
    # max_campaigns_allowed = models.IntegerField(
    #     default=1, 
    #     help_text="Limit how many distinct campaigns/parties the user can manage."
    # )

    # Auditing timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan_tier} ({self.status})"
    
    @property
    def is_active(self):
        """Helper property to quickly check if the user has paid access."""
        return self.status in [self.Status.ACTIVE, self.Status.TRIALING]

    # def reset_usage_quotas(self):
    #     """Method to call via Celery or Cron when a new billing cycle starts."""
    #     self.monthly_audio_minutes_used = 0
    #     self.summaries_generated_count = 0
    #     self.billing_cycle_anchor = timezone.now()
    #     self.save(update_fields=['monthly_audio_minutes_used', 'summaries_generated_count', 'billing_cycle_anchor'])

    class Meta:
        ordering = ['user__username']

class Campaign(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='campaigns')

    def __str__(self):
        return self.name

class Session(models.Model):
    """
    The 'Event' container. It holds metadata about the game night.
    """
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=255)
    date_played = models.DateField()
    description = models.TextField(blank=True, null=True, help_text="Brief blurb about the night")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date_played}"

class Recording(models.Model):
    """
    A session could have multiple audio files (e.g., pre-break and post-break).
    """
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='recording')
    audio_file = models.FileField(upload_to='notetaker/recordings')
    duration_seconds = models.IntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Transcription(models.Model):
    """
    The output from AssemblyAI. Linked to a specific recording.
    """
    recording = models.OneToOneField(Recording, on_delete=models.CASCADE, related_name='transcription')
    assembly_id = models.CharField(max_length=100, unique=True)
    raw_text = models.TextField()
    
    # Store JSON data if you want to keep word-level timestamps or speaker data separately
    utterances_json = models.JSONField(null=True, blank=True) 
    
    processed_at = models.DateTimeField(auto_now_add=True)

class Summary(models.Model):
    """
    The output from Gemini. Linked to a transcription.
    Allows for multiple versions (e.g., 'Combat focus' vs 'Lore focus').
    """
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name='summaries')
    model_used = models.CharField(max_length=50, default="gemini-2.5-flash")
    content = models.TextField(help_text="The Markdown notes")
    
    summary_type = models.CharField(max_length=50, default="standard", help_text="e.g., Full, Combat, or NPC list")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.summary_type.capitalize()} Summary for {self.transcription.recording.session.title}"
    
    class Meta:
        verbose_name_plural = "Summaries"

class CustomVocabulary(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='vocabulary')
    term = models.CharField(max_length=100)
    note = models.CharField(max_length=255, blank=True, help_text="Optional hint for what this is (NPC, Place, etc.)")

    def __str__(self):
        return self.term

    class Meta:
        verbose_name_plural = "Custom Vocabularies"

