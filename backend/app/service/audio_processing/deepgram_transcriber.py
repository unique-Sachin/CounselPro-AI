#!/usr/bin/env python3
import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepgramTranscriber:
    def __init__(self, api_key: Optional[str] = None, output_dir: Optional[str] = None):
        self.api_key = api_key or os.getenv('DEEPGRAM_API_KEY')
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found")
        
        self.client = DeepgramClient(self.api_key)
        
        if output_dir is None:
            current_file = Path(__file__).resolve()
            project_root = current_file.parents[4]
            self.output_dir = project_root / "backend" / "assets" / "transcripts_raw"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir}")

    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"

    def _extract_utterances(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        utterances = []
        dg_utterances = response.get('results', {}).get('utterances', [])
        
        for utterance in dg_utterances:
            utterances.append({
                "speaker": utterance.get('speaker', 0),
                "text": utterance.get('transcript', ''),
                "start_time": self._format_time(utterance.get('start', 0)),
                "end_time": self._format_time(utterance.get('end', 0)),
                "confidence": round(utterance.get('confidence', 0), 2)
            })
        
        return utterances

    def transcribe_chunk(self, chunk_path: str, chunk_index: int) -> str:
        chunk_file = Path(chunk_path)
        output_path = self.output_dir / f"chunk_{chunk_index:03d}.json"
        
        logger.info(f"Transcribing chunk {chunk_index:03d}: {chunk_file.name}")
        
        options = PrerecordedOptions(
            model="nova-2",
            language="en-US",
            punctuate=True,
            diarize=True,
            smart_format=True,
            utterances=True,
            utt_split=0.8
        )
        
        with open(chunk_path, 'rb') as audio_file:
            payload: FileSource = {"buffer": audio_file.read()}
        
        start_time = time.time()
        response = self.client.listen.rest.v("1").transcribe_file(payload, options)  # type: ignore
        processing_time = time.time() - start_time
        
        utterances = self._extract_utterances(response.to_dict())  # type: ignore
        
        formatted_output = {
            "metadata": {
                "chunk_index": chunk_index,
                "chunk_file": f"backend/assets/audio_chunks/{chunk_file.name}",
                "processing_time_seconds": round(processing_time, 2),
                "deepgram_model": "nova-2",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "api_version": "v1"
            },
            "utterances": utterances
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Completed chunk {chunk_index:03d} - {len(utterances)} utterances")
        return str(output_path)

    def transcribe_chunks(self, chunk_paths: List[str]) -> List[str]:
        logger.info(f"Starting transcription of {len(chunk_paths)} chunks")
        
        transcript_paths = []
        for i, chunk_path in enumerate(chunk_paths, 1):
            transcript_path = self.transcribe_chunk(chunk_path, i)
            transcript_paths.append(transcript_path)
        
        return transcript_paths

def main():
    try:
        chunk_paths = sys.argv[1:]
        if not chunk_paths:
            logger.error("No audio files provided")
            sys.exit(1)
        
        transcriber = DeepgramTranscriber()
        transcript_paths = transcriber.transcribe_chunks(chunk_paths)
        
        logger.info(f"Completed transcription of {len(transcript_paths)} files")
        return transcript_paths
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
