from celery import shared_task
from django.conf import settings
from .models import Recording, Transcription, Summary
from .services import AssemblyAIService, GeminiService

@shared_task
def process_transcription(recording_id):
    """
    Fire-and-forget task to submit a recording to AssemblyAI.
    The actual saving of text happens later in the Webhook view.
    """
    recording = None
    transcription = None
    try:
        recording = Recording.objects.get(id=recording_id)
        transcription = recording.transcription #type:ignore

        # 1. Try to get a URL (Works for S3/Cloud) - Fall back to .path (Works for Local dev)
        try:
            audio_source = recording.audio_file.url
            if audio_source.startswith('/'):
                audio_source = recording.audio_file.path
        except (NotImplementedError, AttributeError):
            audio_source = recording.audio_file.path

        # 2. Build the webhook URL (using your Ngrok address from dev.py)
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/notetaker/webhooks/assemblyai/"

        # 3. Submit to AssemblyAI (Using the new .submit() service)
        # This returns an ID immediately, no waiting.
        transcript_info = AssemblyAIService.submit_transcription(audio_source, webhook_url)

        # 4. UPDATE the existing record instead of creating a new one
        transcription.assembly_id = transcript_info.id
        transcription.status = Transcription.Status.PROCESSING
        transcription.save()
        
        return f"Successfully submitted recording {recording_id} to AssemblyAI (ID: {transcript_info.id})"

    except Recording.DoesNotExist:
        return f"Error: Recording {recording_id} not found."
    except Transcription.DoesNotExist:
        return f"Error: Transcription record not found for recording {recording_id}."
    except Exception as e:
        # Only attempt to save if transcription was successfully fetched
        if transcription:
            transcription.status = Transcription.Status.FAILED
            transcription.save()
        return f"Submission failed: {str(e)}"


@shared_task
def process_summary(transcription_id):
    """
    Background task to generate a D&D session summary using Gemini 
    and save it to the database.
    """
    try:
        # 1. Fetch the exact transcription object
        transcription = Transcription.objects.get(id=transcription_id)

        # 2. Call the Gemini Service using the raw text
        summary_text = GeminiService.generate_dnd_summary(transcription.raw_text)
        
        # 3. Create the Summary record
        Summary.objects.create(
            transcription=transcription,
            model_used='gemini',
            summary_type='dnd_session', 
            content=summary_text
        )
        
        return f"Successfully summarized transcription {transcription_id}"

    except Transcription.DoesNotExist:
        return f"Error: Transcription {transcription_id} not found."
    except Exception as e:
        return f"Summarization failed: {str(e)}"