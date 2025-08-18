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
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('DEEPGRAM_API_KEY')
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found")
        
        self.client = DeepgramClient(self.api_key)

    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"

    def _identify_roles(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify speaker roles based on speaking patterns and context.
        """
        if not utterances:
            return {}
        
        # Count words per speaker
        speaker_stats = {}
        for utt in utterances:
            spk = utt["speaker"]
            words = len(utt["text"].split())
            speaker_stats[spk] = speaker_stats.get(spk, 0) + words

        # Get all unique speakers
        all_speakers = list(speaker_stats.keys())
        
        if len(all_speakers) == 1:
            # Only one speaker
            return {"counselor": all_speakers[0]}
        elif len(all_speakers) == 2:
            # Two speakers - identify counselor and student
            first_speaker = utterances[0]["speaker"]
            
            # Guess by talk ratio (counselor typically talks more)
            counselor = max(speaker_stats, key=lambda x: speaker_stats[x])
            student = min(speaker_stats, key=lambda x: speaker_stats[x])
            
            # If first speaker talked a lot, reinforce guess
            if first_speaker != counselor:
                # Flip if mismatch and ratio is not huge
                if speaker_stats[counselor] / speaker_stats[student] < 1.3:
                    counselor, student = student, counselor
            
            return {"counselor": counselor, "student": student}
        else:
            # More than 2 speakers - identify counselor and label others
            counselor = max(speaker_stats, key=lambda x: speaker_stats[x])
            role_mapping = {"counselor": counselor}
            
            # Label other speakers as speaker_2, speaker_3, etc.
            speaker_counter = 2
            for speaker_id in all_speakers:
                if speaker_id != counselor:
                    role_mapping[f"speaker_{speaker_counter}"] = speaker_id
                    speaker_counter += 1
            
            return role_mapping

    def _apply_role_labels(self, utterances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply role labels to utterances based on speaker identification.
        
        Args:
            utterances: List of utterance dictionaries
            
        Returns:
            List of utterances with role labels added
        """
        role_mapping = self._identify_roles(utterances)
        
        # Create reverse mapping (speaker_id -> role)
        speaker_to_role = {v: k for k, v in role_mapping.items()}
        
        # Add role labels to utterances
        labeled_utterances = []
        for utt in utterances:
            labeled_utt = utt.copy()
            speaker_id = utt["speaker"]
            labeled_utt["role"] = speaker_to_role.get(speaker_id, f"speaker_{speaker_id}")
            labeled_utterances.append(labeled_utt)
        
        return labeled_utterances

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
        
        # Apply role labels to the utterances
        labeled_utterances = self._apply_role_labels(utterances)
        
        return labeled_utterances

    def transcribe_chunk(self, chunk_path: str, chunk_name: str) -> Dict[str, Any]:
        chunk_file = Path(chunk_path)
        
        logger.info(f"Transcribing chunk {chunk_name}: {chunk_file.name}")
        
        options = PrerecordedOptions(
            model="nova-3",
            language="en-US",
            punctuate=True,
            diarize=True,
            utterances=True,
            utt_split=0.8
        )
        
        with open(chunk_path, 'rb') as audio_file:
            payload: FileSource = {"buffer": audio_file.read()}
        
        start_time = time.time()
        response = self.client.listen.rest.v("1").transcribe_file(payload, options)  # type: ignore
        processing_time = time.time() - start_time
        
        utterances = self._extract_utterances(response.to_dict())  # type: ignore
        
        # Get role mapping for metadata
        role_mapping = self._identify_roles(utterances)
        
        formatted_output = {
            "metadata": {
                "chunk_name": chunk_name,
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "role_mapping": role_mapping,
                "total_speakers": len(role_mapping)
            },
            "utterances": utterances
        }
        
        # Return the transcript data instead of saving to file
        return formatted_output

    # def transcribe_chunks(self, chunk_paths: List[str]) -> List[str]:
    #     logger.info(f"Starting transcription of {len(chunk_paths)} chunks")
        
    #     transcript_paths = []
    #     for i, chunk_path in enumerate(chunk_paths, 1):
    #         transcript_path = self.transcribe_chunk(chunk_path, i)
    #         transcript_paths.append(transcript_path)
        
    #     return transcript_paths

# def main():
#     try:
#         chunk_paths = sys.argv[1:]
#         if not chunk_paths:
#             logger.error("No audio files provided")
#             sys.exit(1)
        
#         transcriber = DeepgramTranscriber()
#         transcript_paths = transcriber.transcribe_chunks(chunk_paths)
        
#         logger.info(f"Completed transcription of {len(transcript_paths)} files")
#         return transcript_paths
        
#     except Exception as e:
#         logger.error(f"Transcription failed: {e}")
#         sys.exit(1)

# if __name__ == "__main__":
#     main()
