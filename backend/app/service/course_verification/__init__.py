"""
Course Verification Module

This module provides RAG-based course information verification capabilities
for counseling session transcripts using Pinecone and OpenAI.
"""

from .course_verifier import CourseVerifier, CourseInfo, VerificationResult

__all__ = ['CourseVerifier', 'CourseInfo', 'VerificationResult']
