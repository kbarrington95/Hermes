from celery import shared_task
from .models import Recording, Transcription, Summary
from .services import AssemblyAIService, GeminiService

@shared_task
def process_transcription(recording_id):
    """
    Background task to process a recording through AssemblyAI and save it to the DB.
    """
    try:
        # 1. Fetch the exact recording
        recording = Recording.objects.get(id=recording_id)

        # 2. Call the service and get the transcript object back
        # (This uses the exact file path from your FileField)
        transcript = AssemblyAIService.transcribe(recording.audio_file.path) 
        
        # 3. If you want to save the JSON utterances, extract them into a list of dicts
        utterances_data = None
        if getattr(transcript, 'utterances', None):
             # AssemblyAI utterances are objects, we convert them to dictionaries for JSONField
             utterances_data = [
                 {"speaker": u.speaker, "text": u.text, "start": u.start, "end": u.end} 
                 for u in transcript.utterances #type:ignore
             ]

        # 4. Create the Transcription record
        Transcription.objects.create(
            recording=recording,
            assembly_id=transcript.id,  # Capturing the required ID
            raw_text=transcript.text,
            utterances_json=utterances_data
        )
        
        return f"Successfully transcribed recording {recording_id}"

    except Recording.DoesNotExist:
        return f"Error: Recording {recording_id} not found."
    except Exception as e:
        return f"Transcription failed: {str(e)}"
    

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