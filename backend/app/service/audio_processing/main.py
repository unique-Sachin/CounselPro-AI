import json
import os
import shutil
import sys
from pathlib import Path

import whisper

AUDIO_PATH = (Path(__file__).resolve().parent / ".." / "assets" / "file.wav").resolve()
OUTPUT_JSON = Path(__file__).resolve().parent / "session_transcript1.json"


def require_ffmpeg():
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found. Install with 'brew install ffmpeg' and ensure it's on PATH.")


def diarize_segments(audio_path: Path):
    # Enable diarization only if HF_TOKEN is set
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        return []

    from pyannote.audio import Pipeline  # lazy import
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)
    diarization = pipeline(str(audio_path))  # cast Path -> str

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({"speaker": speaker, "start": turn.start, "end": turn.end})
    return segments


def main():
    require_ffmpeg()

    if not AUDIO_PATH.exists():
        sys.exit(f"Audio file not found: {AUDIO_PATH}")

    # Transcription (cast Path -> str)
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(AUDIO_PATH), word_timestamps=True)

    # Diarization (optional)
    # speaker_segments = diarize_segments(AUDIO_PATH)

    # Merge by timestamps
    output = []
    for segment in result.get("segments", []):
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()

        speaker_label = "Unknown"
        # for seg in speaker_segments:
        #     if start >= seg["start"] and end <= seg["end"]:
        #         speaker_label = seg["speaker"]
        #         break

        output.append({
            "speaker": speaker_label,
            "text": text,
            "start_time": f"{int(start//3600):02}:{int((start%3600)//60):02}:{int(start%60):02}",
            "end_time": f"{int(end//3600):02}:{int((end%3600)//60):02}:{int(end%60):02}",
        })

    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()