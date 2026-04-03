#!/usr/bin/env python3
"""
Initialize vector database with sample data
This script loads the sample TXT/PDF documents into the FAISS vector database
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rag.vector_db import VectorDatabase
from src.rag.document_processor import DocumentProcessor

def load_pdf_documents(directory, source_name):
    """Load PDF documents from directory using DocumentProcessor"""
    docs = DocumentProcessor.process_pdf_directory(str(directory))
    return docs

def load_txt_documents(directory, source_name):
    """Load TXT documents from directory"""
    documents = []
    txt_files = list(Path(directory).glob('*.txt'))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split into chunks for better retrieval
            chunks = content.split('\n\n')  # Split by double newline
            
            doc_index = 0
            for chunk in chunks:
                if chunk.strip():  # Skip empty chunks
                    documents.append({
                        'content': chunk.strip(),
                        'file_name': txt_file.name,
                        'page': doc_index
                    })
                    doc_index += 1
        except Exception as e:
            print(f"Error loading {txt_file}: {e}")
    
    return documents

def main():
    print("=" * 70)
    print("Initializing GreenMind Vector Database")
    print("=" * 70)
    print()
    
    try:
        # Initialize vector database
        print("[1/3] Initializing vector database...")
        vector_db = VectorDatabase()
        print("      [OK] Vector DB initialized")
        
        # Load and process environmental policies
        print("\n[2/3] Loading environmental policies...")
        policies_dir = project_root / 'data' / 'environmental_policies'
        if policies_dir.exists():
            pdf_count = len(list(policies_dir.glob('*.pdf')))
            if pdf_count > 0:
                policies_docs = load_pdf_documents(str(policies_dir), 'policies')
                if policies_docs:
                    print(f"      Found {len(policies_docs)} policy chunks from {pdf_count} PDF files")
                    vector_db.add_documents(policies_docs, source='policies')
                    print("      [OK] Policies indexed (PDF)")
                else:
                    print("      [WARNING] No content extracted from policy PDFs")
            else:
                print("      [WARNING] No policy PDF documents found")
        else:
            print(f"      [ERROR] Directory not found: {policies_dir}")
        
        # Load and process environmental effects
        print("\n[3/3] Loading environmental effects...")
        effects_dir = project_root / 'data' / 'environmental_effects'
        if effects_dir.exists():
            pdf_count = len(list(effects_dir.glob('*.pdf')))
            if pdf_count > 0:
                effects_docs = load_pdf_documents(str(effects_dir), 'effects')
                if effects_docs:
                    print(f"      Found {len(effects_docs)} effect chunks from {pdf_count} PDF files")
                    vector_db.add_documents(effects_docs, source='effects')
                    print("      [OK] Effects indexed (PDF)")
                else:
                    print("      [WARNING] No content extracted from PDFs")
            else:
                effects_docs = load_txt_documents(str(effects_dir), 'effects')
                if effects_docs:
                    print(f"      Found {len(effects_docs)} effect chunks from {len(list(effects_dir.glob('*.txt')))} files")
                    vector_db.add_documents(effects_docs, source='effects')
                    print("      [OK] Effects indexed")
                else:
                    print("      [WARNING] No effects documents found")
        else:
            print(f"      [ERROR] Directory not found: {effects_dir}")
        
        # Save vector database
        print("\n[*] Saving vector database...")
        vector_db.save()
        
        # Print statistics
        stats = vector_db.get_stats()
        print("\n" + "=" * 70)
        print("VECTOR DATABASE INITIALIZATION COMPLETE")
        print("=" * 70)
        print(f"Database path: {stats['db_path']}")
        print(f"Vector store ready: {stats['vector_store_ready']}")
        if stats['metadata']:
            print(f"Sources indexed: {list(stats['metadata'].keys())}")
            for source, info in stats['metadata'].items():
                print(f"  - {source}: {info.get('doc_count', 0)} documents")
        print()
        print("[SUCCESS] Vector database ready for queries!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
