from django.db import models

class Campaign(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='recordings')
    audio_file = models.FileField(upload_to='recordings/%Y/%m/%d/')
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

class CustomVocabulary(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='vocabulary')
    term = models.CharField(max_length=100)
    note = models.CharField(max_length=255, blank=True, help_text="Optional hint for what this is (NPC, Place, etc.)")

    def __str__(self):
        return self.term

    class Meta:
        verbose_name_plural = "Custom Vocabularies"