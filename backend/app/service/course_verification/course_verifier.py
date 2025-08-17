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
                 openai_model: str = "gpt-4o-mini",
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
        Verify course information across an entire transcript.
        
        Args:
            transcript_data: Full transcript data with utterances
            
        Returns:
            Combined verification results
        """
        try:
            # Extract all utterances text
            utterances = transcript_data.get('utterances', [])
            
            # Combine all counselor utterances
            counselor_text = []
            for utterance in utterances:
                if utterance.get('role') == 'counselor':
                    counselor_text.append(utterance.get('text', ''))
            
            # Combine into text
            full_counselor_text = ' '.join(counselor_text)
            
            if not full_counselor_text.strip():
                return {
                    "courses_mentioned": [],
                    "overall_summary": "No counselor utterances found for verification",
                    "accuracy_score": 0.0,
                    "red_flags": ["No counselor content to verify"]
                }
            
            # Verify the counselor text
            result = self.verify_transcript_chunk(full_counselor_text)
            
            # Add session metadata
            result['session_metadata'] = {
                'session_id': transcript_data.get('session_id'),
                'total_utterances': len(utterances),
                'counselor_utterances': len(counselor_text)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying full transcript: {e}")
            return {
                "courses_mentioned": [],
                "overall_summary": f"Full transcript verification failed: {str(e)}",
                "accuracy_score": 0.0,
                "red_flags": ["System error during full transcript verification"],
                "session_metadata": {}
            }
