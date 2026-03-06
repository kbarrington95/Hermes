import assemblyai as aai
from google import genai
from django.conf import settings


class AssemblyAIService:
    
    @staticmethod
    def transcribe(audio_source): # Renamed from file_path to reflect URL/Path flexibility
        """
        Uses the SDK to transcribe the file or URL.
        Blocking call - will wait for completion.
        """
        # --- NEW CODE ADDED ---
        # Explicitly set the API key from your environment-aware settings
        aai.settings.api_key = settings.ASSEMBLY_AI_API_KEY
        # ----------------------
        
        # 1. Configuration
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best,
            speaker_labels=True,
            # Boosted terms for your specific campaign
            word_boost=["Zaki", "Ool", "Alis", "Sama", "Grunk", "Illithinoch"]
        )

        # 2. Transcribe
        transcriber = aai.Transcriber()
        
        try:
            # The SDK detects if audio_source is a local path or an S3 URL
            # It handles upload + polling automatically
            transcript = transcriber.transcribe(audio_source, config=config)
            
            if transcript.status == aai.TranscriptStatus.error:
                 raise Exception(f"AssemblyAI Error: {transcript.error}")
                 
            return transcript 

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
        
class GeminiService:
    
    @staticmethod
    def generate_dnd_summary(transcript_text):
        """
        Takes raw transcript text and uses Gemini to generate 
        structured D&D session notes.
        """
        # 1. Initialize the client using Django settings
        if not getattr(settings, 'GEMINI_API_KEY', None):
             raise ValueError("GEMINI_API_KEY is missing from Django settings.")
             
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # 2. Define the exact D&D Prompt Template
        dnd_prompt_template = """
            You are an expert Dungeons & Dragons Campaign Manager and note-taker. Your task is to analyze the provided session transcript and produce structured, actionable notes for the Dungeon Master. Do not include any introductory or concluding remarks. The output must be Markdown-formatted and adhere strictly to the sections outlined below.

            1. Session Summary & Key Decisions
            Try to create a clever title for the last session that accurately describes what happened. Bold the title. 
            Provide a 6-10 sentence summary of the session's major plot points. (bold character names, locations and key items if they are included in the summary)

            2. Key Party Decisions
            List up to 3 important decisions made by the party (bulleted list)

            3. Party Next Steps
            Immediate Next Steps: Provide 2-3 specific, actionable steps the Party is likely to take next session.

            4. Party Resources
            List if any party members were knocked unconcious (brought down to 0 health points)
            List if the party took any short or long rests.
            List all consumable resources used by the party segmented by party memeber. (e.g. healing potions, consumables, spell slots)
            List which party member did the most damage OVERALL and which party member killed the most enemies OVERALL.

            5. NPC & Location Tracker
            NPCs Discussed: List all unique names, a one-sentence description, and their location. If any of their status or location significantly changed list that change.
            New Locations: List all new geographical locations or structures mentioned.

            6. Quotes!
            List 3-5 funny quotes made by the party. Focus on ones which caused a lot of laughs or follow up jokes.

            ---
            [TRANSCRIPT START]
            {transcript_content}
            [TRANSCRIPT END]
            """
        
        # 3. Inject the text
        final_prompt = dnd_prompt_template.format(transcript_content=transcript_text)

        try:
            # 4. Call the Gemini API
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=final_prompt,
                config=genai.types.GenerateContentConfig(temperature=0.2)
            )
            return response.text
            
        except Exception as e:
            raise Exception(f"Gemini summarization failed: {str(e)}")