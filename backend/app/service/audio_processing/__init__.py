"""
Audio Processing Service Module

This module provides utilities for audio processing and transcription,
particularly for converting audio chunks to text using speech recognition APIs.
"""

from .deepgram_transcriber import DeepgramTranscriber

__all__ = ['DeepgramTranscriber']
