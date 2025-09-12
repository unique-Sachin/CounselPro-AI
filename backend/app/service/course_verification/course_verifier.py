#!/usr/bin/env python3
"""
Course Information Verification Service

This module verifies course information mentioned in counseling session transcripts
against the official course catalog using RAG (Retrieval Augmented Generation).
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CourseInfo(BaseModel):
    """Structured model for course information comparison."""
    name: str = Field(description="Course name mentioned in transcript")
    claimed_duration: Optional[str] = Field(description="Duration claimed by counselor")
    claimed_fee: Optional[str] = Field(description="Fee claimed by counselor")
    catalog_duration: Optional[str] = Field(description="Actual duration from catalog")
    catalog_fee: Optional[str] = Field(description="Actual fee from catalog")
    match_status: str = Field(description="MATCH, MISMATCH, or PARTIAL_MATCH")
    confidence_score: float = Field(description="Confidence in the verification (0-1)")
    notes: str = Field(description="Detailed explanation of comparison")


class VerificationResult(BaseModel):
    """Complete verification result structure."""
    courses_mentioned: List[CourseInfo] = Field(description="List of courses analyzed")
    overall_summary: str = Field(description="Summary of verification findings")
    accuracy_score: float = Field(description="Overall accuracy score (0-1)")
    red_flags: List[str] = Field(description="Critical mismatches or concerns")


class CourseVerifier:
    """
    Main class for verifying course information using RAG.
    """
    
    def __init__(self, 
                 pinecone_index_name: str = "counselpro-ai",
                 openai_model: str = "gpt-4.1",
                 embedding_model: str = "text-embedding-3-large"):
        """
        Initialize the CourseVerifier.
        """
        self.pinecone_index_name = pinecone_index_name
        self.openai_model = openai_model
        self.embedding_model = embedding_model
        
        # Validate environment variables
        required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
        for var in required_vars:
            if not os.getenv(var):
                raise ValueError(f"Environment variable {var} is required")
        
        self._setup_components()
    
    def _setup_components(self):
        """Initialize LangChain components."""
        try:
            # Setup embeddings
            self.embeddings = OpenAIEmbeddings(model=self.embedding_model)
            
            # Setup vector store
            self.vectorstore = PineconeVectorStore(
                index_name=self.pinecone_index_name, 
                embedding=self.embeddings
            )
            
            # Setup retriever
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 5}  # Retrieve top 5 relevant documents
            )
            
            # Setup LLM
            self.llm = ChatOpenAI(
                model=self.openai_model,
                temperature=0.1  # Low temperature for consistency
            )
            
            # Setup output parser
            self.output_parser = PydanticOutputParser(pydantic_object=VerificationResult)
            
            # Setup prompt template
            self._setup_prompt()
            
            logger.info("CourseVerifier components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CourseVerifier: {e}")
            raise
    
    def _setup_prompt(self):
        """Setup the verification prompt template."""
        
        # Load prompt from external file
        prompt_file = os.path.join(os.path.dirname(__file__), "course_verification_prompt.txt")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {prompt_file}. Using default prompt.")
            # Fallback to basic prompt
            prompt_template = """
                You are a course information verification assistant. Verify whether course information 
                mentioned in counseling transcripts is accurate compared to the official course catalog.

                TRANSCRIPT EXCERPT:
                {transcript_chunk}

                OFFICIAL COURSE CATALOG (Retrieved Context):
                {retrieved_docs}

                Compare the transcript claims against the catalog information and provide analysis.

                {format_instructions}
                """
        
        self.prompt = ChatPromptTemplate.from_template(prompt_template)
    
    def verify_transcript_chunk(self, transcript_chunk: str) -> Dict[str, Any]:
        """
        Verify course information in a transcript chunk.
        
        Args:
            transcript_chunk: Text chunk from counseling session transcript
            
        Returns:
            Dictionary containing verification results
        """
        try:
            logger.info("Starting course verification for transcript chunk")
            
            # Retrieve relevant documents from catalog
            docs = self.retriever.get_relevant_documents(transcript_chunk)
            
            # Combine retrieved documents
            retrieved_docs = "\n\n---\n\n".join([doc.page_content for doc in docs])
            
            logger.info(f"Retrieved {len(docs)} relevant documents")
            
            # Format prompt with context and format instructions
            formatted_prompt = self.prompt.format(
                transcript_chunk=transcript_chunk,
                retrieved_docs=retrieved_docs,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse structured output
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Ensure we have a string
            if isinstance(response_text, list):
                response_text = ' '.join(str(item) for item in response_text)
            elif not isinstance(response_text, str):
                response_text = str(response_text)
            
            verification_result = self.output_parser.parse(response_text)
            
            logger.info("Course verification completed successfully")
            
            return verification_result.model_dump()
            
        except Exception as e:
            logger.error(f"Error during course verification: {e}")
            return {
                "courses_mentioned": [],
                "overall_summary": f"Verification failed due to error: {str(e)}",
                "accuracy_score": 0.0,
                "red_flags": ["System error during verification"]
            }
    
    def verify_full_transcript(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify course information across an entire transcript with context-aware processing.
        
        Args:
            transcript_data: Full transcript data with utterances
            
        Returns:
            Combined verification results
        """
        try:
            # Extract all utterances text
            utterances = transcript_data.get('utterances', [])
            
            # Combine ALL utterances regardless of role
            all_text = []
            counselor_text = []
            student_text = []
            
            for utterance in utterances:
                text = utterance.get('text', '')
                all_text.append(text)
                
                # Still separate by role for metadata analysis
                if utterance.get('role') == 'counselor':
                    counselor_text.append(text)
                else:  # Assuming non-counselor is student
                    student_text.append(text)
            
            # Combine all text for verification
            full_transcript_text = ' '.join(all_text)
            
            if not full_transcript_text.strip():
                return self._empty_result("No transcript content found for verification")
            
            logger.info(f"Processing transcript with {len(full_transcript_text.split())} words")
            
            # Step 1: Extract course-relevant content first
            relevant_content = self._extract_course_relevant_content(full_transcript_text)
            
            if not relevant_content.strip():
                return self._empty_result("No course-related content found in transcript")
            
            # Step 2: Estimate tokens and decide processing strategy
            estimated_tokens = self._estimate_tokens(relevant_content)
            max_single_chunk_tokens = 40000  # Conservative limit for GPT-4o-mini
            
            logger.info(f"Estimated tokens for relevant content: {estimated_tokens}")
            
            if estimated_tokens <= max_single_chunk_tokens:
                # Process as single chunk
                logger.info("Processing as single chunk")
                result = self.verify_transcript_chunk(relevant_content)
            else:
                # Process with chunking
                logger.info("Processing with chunking strategy")
                result = self._verify_with_chunking(relevant_content, transcript_data)
            
            # Add session metadata with role breakdown
            result['session_metadata'] = {
                'session_id': transcript_data.get('session_id'),
                'total_utterances': len(utterances),
                'counselor_utterances': len(counselor_text),
                'student_utterances': len(student_text),
                'verification_scope': 'all_speakers',
                'content_filtering': 'course_relevant_only',
                'original_length_words': len(full_transcript_text.split()),
                'filtered_length_words': len(relevant_content.split()),
                'estimated_tokens': int(estimated_tokens),
                'processing_method': 'chunked' if estimated_tokens > max_single_chunk_tokens else 'single',
                'diarization_note': 'Course information verified from all participants to ensure accuracy'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying full transcript: {e}")
            return self._error_result(str(e))

    def _extract_course_relevant_content(self, transcript_text: str) -> str:
        """Extract only course-relevant portions of transcript."""
        
        # Course-related keywords
        course_keywords = [
            'course', 'program', 'degree', 'certificate', 'diploma', 'curriculum',
            'tuition', 'fee', 'cost', 'duration', 'semester', 'year', 'credit',
            'requirement', 'prerequisite', 'admission', 'enrollment', 'major',
            'specialization', 'department', 'faculty', 'graduation', 'class',
            'bachelor', 'master', 'associate', 'phd', 'doctorate', 'undergraduate',
            'graduate', 'study', 'studies', 'education', 'academic', 'school',
            'university', 'college', 'institute', 'training', 'certification'
        ]
        
        sentences = transcript_text.split('.')
        relevant_sentences = []
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in course_keywords):
                # Include some context (previous and next sentence)
                start_idx = max(0, i - 1)
                end_idx = min(len(sentences), i + 2)
                context = '. '.join(sentences[start_idx:end_idx])
                relevant_sentences.append(context.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_sentences = []
        for sentence in relevant_sentences:
            if sentence not in seen:
                seen.add(sentence)
                unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in text using a simple word-based approximation."""
        # Simple approximation: 1 word ≈ 1.3 tokens for English text
        # This is conservative and works well for GPT models
        return int(len(text.split()) * 1.3)

    def _verify_with_chunking(self, relevant_content: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process transcript in overlapping chunks."""
        
        # Determine optimal chunk size based on content length
        estimated_tokens = self._estimate_tokens(relevant_content)
        chunk_size, overlap = self._get_adaptive_chunk_size(int(estimated_tokens))
        
        # Split into words
        words = relevant_content.split()
        chunks = []
        
        # Create overlapping chunks
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        logger.info(f"Processing transcript in {len(chunks)} chunks (size: {chunk_size}, overlap: {overlap})")
        
        # Verify each chunk
        all_courses = []
        all_red_flags = []
        accuracy_scores = []
        summaries = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            try:
                chunk_result = self.verify_transcript_chunk(chunk)
                
                # Collect results
                all_courses.extend(chunk_result.get('courses_mentioned', []))
                all_red_flags.extend(chunk_result.get('red_flags', []))
                accuracy_scores.append(chunk_result.get('accuracy_score', 0.0))
                summaries.append(chunk_result.get('overall_summary', ''))
                
            except Exception as e:
                logger.warning(f"Error processing chunk {i+1}: {e}")
                all_red_flags.append(f"Processing error in chunk {i+1}: {str(e)}")
        
        # Merge and deduplicate results
        return self._merge_chunk_results(
            all_courses, all_red_flags, accuracy_scores, summaries, len(chunks), chunk_size
        )

    def _get_adaptive_chunk_size(self, estimated_tokens: int) -> tuple[int, int]:
        """Determine optimal chunk size based on content length."""
        
        if estimated_tokens < 20000:
            return 6000, 300    # Large chunks for short content
        elif estimated_tokens < 50000:
            return 4000, 200    # Medium chunks
        elif estimated_tokens < 100000:
            return 3000, 150    # Smaller chunks for long content
        else:
            return 2000, 100    # Very small chunks for very long content

    def _merge_chunk_results(self, all_courses: List[Dict], all_red_flags: List[str], 
                           accuracy_scores: List[float], summaries: List[str], 
                           total_chunks: int, chunk_size: int) -> Dict[str, Any]:
        """Merge results from multiple chunks."""
        
        # Deduplicate courses by name (case-insensitive)
        unique_courses = {}
        for course in all_courses:
            course_name = course.get('name', '').lower().strip()
            if course_name and course_name not in unique_courses:
                unique_courses[course_name] = course
            elif course_name:
                # Keep the one with higher confidence
                existing_confidence = unique_courses[course_name].get('confidence_score', 0)
                new_confidence = course.get('confidence_score', 0)
                if new_confidence > existing_confidence:
                    unique_courses[course_name] = course
        
        # Deduplicate red flags
        unique_red_flags = list(set(filter(None, all_red_flags)))
        
        # Calculate overall accuracy
        overall_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        
        # Combine summaries
        valid_summaries = [s for s in summaries if s and s.strip()]
        if valid_summaries:
            combined_summary = f"Multi-chunk analysis of {len(valid_summaries)} sections completed. "
            if len(valid_summaries) <= 3:
                combined_summary += " | ".join(valid_summaries)
            else:
                combined_summary += f"Found {len(list(unique_courses.values()))} unique courses mentioned across {total_chunks} chunks."
        else:
            combined_summary = f"Processed {total_chunks} chunks but no significant course information found."
        
        return {
            "courses_mentioned": list(unique_courses.values()),
            "overall_summary": combined_summary,
            "accuracy_score": overall_accuracy,
            "red_flags": unique_red_flags
        }

    def _empty_result(self, message: str) -> Dict[str, Any]:
        """Return empty result with message."""
        return {
            "courses_mentioned": [],
            "overall_summary": message,
            "accuracy_score": 0.0,
            "red_flags": []
        }

    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return error result."""
        return {
            "courses_mentioned": [],
            "overall_summary": f"Verification failed: {error_message}",
            "accuracy_score": 0.0,
            "red_flags": ["System error during verification"],
            "session_metadata": {}
        }
