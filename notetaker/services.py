# services.py
import assemblyai as aai
from django.conf import settings

# Initialize once with your API key from settings
aai.settings.api_key = settings.ASSEMBLY_AI_API_KEY

class AssemblyAIService:
    
    @staticmethod
    def transcribe(file_path):
        """
        Uses the SDK to transcribe the file.
        Blocking call - will wait for completion.
        """
        
        # 1. Configuration (Move your D&D list here or pass it in)
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best, # or "universal"
            speaker_labels=True,
            word_boost=["Zaki", "Ool", "Alis", "Sama", "Grunk", "Illithinoch"]
        )

        # 2. Transcribe
        transcriber = aai.Transcriber()
        
        try:
            # The SDK handles upload + polling automatically
            transcript = transcriber.transcribe(file_path, config=config)
            
            if transcript.status == aai.TranscriptStatus.error:
                 raise Exception(f"AssemblyAI Error: {transcript.error}")
                 
            return transcript # Returns the Object, not a dict

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")