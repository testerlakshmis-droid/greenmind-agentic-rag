# Document processor for PDFs

import os
from pathlib import Path
from typing import List, Dict
from PyPDF2 import PdfReader
import logging

logger = logging.getLogger("GreenMind")

class DocumentProcessor:
    """Process PDF documents and extract text"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Extracted text
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    @staticmethod
    def process_pdf_directory(directory: str) -> List[Dict]:
        """
        Process all PDFs in a directory
        
        Args:
            directory: Path to directory containing PDFs
        
        Returns:
            List of documents with content and metadata
        """
        documents = []
        pdf_dir = Path(directory)
        
        if not pdf_dir.exists():
            logger.warning(f"Directory not found: {directory}")
            return documents
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return documents
        
        for pdf_file in pdf_files:
            logger.info(f"Processing: {pdf_file.name}")
            
            # Extract text
            content = DocumentProcessor.extract_text_from_pdf(str(pdf_file))
            
            if content.strip():
                # Split into chunks
                chunks = DocumentProcessor.chunk_text(content, chunk_size=500, overlap=100)
                
                for idx, chunk in enumerate(chunks):
                    documents.append({
                        'file_name': pdf_file.name,
                        'content': chunk,
                        'page': idx,
                        'file_size': pdf_file.stat().st_size
                    })
                
                logger.info(f"Extracted {len(chunks)} chunks from {pdf_file.name}")
        
        return documents
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Chunk text into smaller sections
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    @staticmethod
    def validate_pdf_files(directory: str) -> Dict:
        """
        Validate PDF files in directory
        
        Args:
            directory: Path to directory
        
        Returns:
            Validation report
        """
        pdf_dir = Path(directory)
        report = {
            'directory': directory,
            'exists': pdf_dir.exists(),
            'pdf_count': 0,
            'total_size': 0,
            'status': 'N/A'
        }
        
        if not pdf_dir.exists():
            report['status'] = 'Directory not found'
            return report
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        report['pdf_count'] = len(pdf_files)
        
        for pdf_file in pdf_files:
            report['total_size'] += pdf_file.stat().st_size
        
        if pdf_files:
            report['status'] = f"Valid ({len(pdf_files)} PDFs)"
        else:
            report['status'] = "No PDFs found"
        
        return report
