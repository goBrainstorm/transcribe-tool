# main functinality to transcribe a recording with whisper.cpp
# import whisper.cpp as whisper
import file_handling

def get_example_transcription_with_date():
    date = "2026-01-20T14:30:00"
    transcribtion = "Today we discussed the new project timeline and assigned tasks to team members. John will handle the backend development while Sarah focuses on the frontend. We agreed to have daily standups at 9 AM starting next week."
    summary = "Team meeting about project timeline and task assignments with daily standup schedule."
    tags = ["meeting", "project-planning", "team"]
    language = "en"
    return [date, transcribtion, summary, tags, language]

def get_example_transcription_without_date():
    date = None
    transcribtion = "Quick voice memo: Remember to follow up with the client about the contract revisions. They mentioned concerns about the delivery date in section 3.2. Need to prepare a response by end of day tomorrow."
    summary = "Voice memo reminder about client contract follow-up regarding delivery date concerns."
    tags = ["reminder", "client", "contract", "urgent"]
    language = "en"
    return [date, transcribtion, summary, tags, language]

def transcribe_recording(recording_path, model_size: str = "models/whisper.cpp/ggml-tiny.bin"):
    # TODO: insert logic to transcribe recording with the use of file_handling.py
    pass

def main():
    # get available models
    file_handler = file_handling.FileHandler()

    


if __name__ == "__main__":
    main()