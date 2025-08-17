#!/usr/bin/env python3
"""
Course Catalog Indexer

This module creates and populates a Pinecone vector database with course catalog information.
"""

import os
import logging
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CourseCatalogIndexer:
    """
    Creates and manages the course catalog Pinecone index.
    """
    
    def __init__(self, 
                 index_name: str = "counselpro-ai",
                 embedding_model: str = "text-embedding-3-large"):
        
        self.index_name = index_name
        self.embedding_model = embedding_model
        self.dimension = 3072  # text-embedding-3-large dimension
        
        # Validate environment variables
        if not os.getenv("PINECONE_API_KEY"):
            raise ValueError("PINECONE_API_KEY environment variable is required")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self._setup_pinecone()
        self._setup_embeddings()
    
    def _setup_pinecone(self):
        """Initialize Pinecone client and check/create index."""
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            
            # Check if index exists
            existing_indexes = self.pc.list_indexes().names()
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                logger.info(f"Index {self.index_name} created successfully")
            else:
                logger.info(f"Using existing index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup Pinecone: {e}")
            raise
    
    def _setup_embeddings(self):
        """Initialize OpenAI embeddings."""
        try:
            self.embeddings = OpenAIEmbeddings(model=self.embedding_model)
            logger.info(f"Embeddings initialized with model: {self.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to setup embeddings: {e}")
            raise
    
    def load_documents_from_directory(self, directory_path: str) -> List[Document]:
        """
        Load documents from a directory containing course catalog files.
        
        Args:
            directory_path: Path to directory containing course files
            
        Returns:
            List of LangChain Document objects
        """
        try:
            documents = []
            directory = Path(directory_path)
            
            if not directory.exists():
                raise ValueError(f"Directory {directory_path} does not exist")
            
            # Load files
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        docs = []
                        if file_path.suffix.lower() == '.pdf':
                            loader = PyPDFLoader(str(file_path))
                            docs = loader.load()
                            documents.extend(docs)
                        elif file_path.suffix.lower() == '.docx':
                            loader = Docx2txtLoader(str(file_path))
                            docs = loader.load()
                            documents.extend(docs)
                        elif file_path.suffix.lower() in ['.txt', '.md']:
                            loader = TextLoader(str(file_path), encoding='utf-8')
                            docs = loader.load()
                            documents.extend(docs)
                        
                        logger.info(f"Loaded {len(docs)} documents from {file_path}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to load {file_path}: {e}")
            
            logger.info(f"Total documents loaded: {len(documents)}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            raise
    
    def load_documents_from_file(self, file_path: str) -> List[Document]:
        """
        Load documents from a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of LangChain Document objects
        """
        try:
            documents = []
            path = Path(file_path)
            
            if not path.exists():
                raise ValueError(f"File {file_path} does not exist")
            
            if path.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(path))
                documents = loader.load()
            elif path.suffix.lower() == '.docx':
                loader = Docx2txtLoader(str(path))
                documents = loader.load()
            elif path.suffix.lower() in ['.txt', '.md']:
                loader = TextLoader(str(path), encoding='utf-8')
                documents = loader.load()
            
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load documents from {file_path}: {e}")
            raise
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks for embedding.
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of document chunks
        """
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            chunks = text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} document chunks")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk documents: {e}")
            raise
    
    def index_documents_with_ids(self, documents: List[Document], file_uid: str) -> int:
        """
        Index documents with predictable IDs for later removal.
        
        Args:
            documents: List of document chunks to index
            file_uid: UUID of the source file
            
        Returns:
            Number of chunks indexed
        """
        try:
            logger.info(f"Starting to index {len(documents)} documents with custom IDs...")
            
            # Create custom IDs for each document
            ids = [f"{file_uid}_chunk_{i}" for i in range(len(documents))]
            
            # Create vector store and add documents with custom IDs
            vectorstore = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings
            )
            
            vectorstore.add_documents(documents=documents, ids=ids)
            
            logger.info(f"Documents successfully indexed with IDs into Pinecone")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to index documents with IDs: {e}")
            raise
    
    def unindex_file(self, file_uid: str, chunk_count: int):
        """
        Remove specific file's vectors from Pinecone.
        
        Args:
            file_uid: UUID of the file to unindex
            chunk_count: Number of chunks to remove
        """
        try:
            logger.info(f"Starting to unindex {chunk_count} chunks for file {file_uid}")
            
            # Generate IDs to delete
            ids_to_delete = [f"{file_uid}_chunk_{i}" for i in range(chunk_count)]
            
            # Get Pinecone index and delete vectors
            index = self.pc.Index(self.index_name)
            index.delete(ids=ids_to_delete)
            
            logger.info(f"Successfully unindexed {chunk_count} chunks for file {file_uid}")
            
        except Exception as e:
            logger.error(f"Failed to unindex file {file_uid}: {e}")
            raise


def main():
    """
    Main function to setup the course catalog index from your data.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python catalog_indexer.py <path_to_course_catalog_directory>")
        print("\nExample:")
        print("python catalog_indexer.py /path/to/your/course/pdfs/")
        sys.exit(1)
    
    catalog_directory = sys.argv[1]
    
    try:
        print("🚀 Setting up Course Catalog Index")
        print("=" * 50)
        
        # Initialize indexer
        indexer = CourseCatalogIndexer()
        
        # Load documents
        print(f"📄 Loading documents from: {catalog_directory}")
        documents = indexer.load_documents_from_directory(catalog_directory)
        
        if not documents:
            print("❌ No documents found to index")
            sys.exit(1)
        
        # Chunk documents
        print("✂️  Chunking documents...")
        chunks = indexer.chunk_documents(documents)
        
        # Index documents
        print("🔍 Indexing documents into Pinecone...")
        indexer.index_documents_with_ids(chunks, "cli_batch")
        
        print("\n✅ Course catalog setup completed successfully!")
        print("You can now run the course verification system.")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
