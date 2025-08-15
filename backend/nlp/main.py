from pyannote.audio import Pipeline
import whisper
import json

# 1. Diarization
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token="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")
diarization = pipeline("session.wav")

# Convert diarization to list of segments
speaker_segments = []
for turn, _, speaker in diarization.itertracks(yield_label=True):
    speaker_segments.append({
        "speaker": speaker,
        "start": turn.start,
        "end": turn.end
    })

# 2. Transcription
model = whisper.load_model("large-v3")
result = model.transcribe("session.wav", word_timestamps=True)

# 3. Merge by timestamps
output = []
for segment in result['segments']:
    start = segment['start']
    end = segment['end']
    text = segment['text'].strip()
    
    # Find matching speaker
    speaker_label = "Unknown"
    for seg in speaker_segments:
        if start >= seg['start'] and end <= seg['end']:
            speaker_label = seg['speaker']
            break
    
    output.append({
        "speaker": speaker_label,
        "text": text,
        "start_time": f"{int(start//3600):02}:{int((start%3600)//60):02}:{int(start%60):02}",
        "end_time": f"{int(end//3600):02}:{int((end%3600)//60):02}:{int(end%60):02}"
    })

# Save JSON
with open("session_transcript.json", "w") as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))