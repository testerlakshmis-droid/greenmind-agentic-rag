# Vector Database management for FAISS

import pickle
from pathlib import Path
from typing import List, Dict, Tuple

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        from langchain.embeddings.huggingface import HuggingFaceEmbeddings
try:
    from langchain_community.vectorstores import FAISS
except ImportError:
    from langchain.vectorstores import FAISS

class VectorDatabase:
    """Manages FAISS vector database for document retrieval"""
    
    def __init__(self, db_path="vector_db/faiss_index", 
                 embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vector_store = None
        self.metadata = {}
        
        # Load existing database if available
        self._load_or_create()
    
    def _load_or_create(self):
        """Load existing FAISS index or create new one"""
        index_file = self.db_path / "index.faiss"
        metadata_path = self.db_path / "metadata.pkl"
        
        if index_file.exists() and metadata_path.exists():
            try:
                # Guard against zero-byte corrupted files
                if index_file.stat().st_size == 0 or metadata_path.stat().st_size == 0:
                    print(f"Warning: Empty database files detected. Creating new vector database.")
                    self.vector_store = None
                    return
                
                self.vector_store = FAISS.load_local(
                    str(self.db_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                
                if self.vector_store is None:
                    print(f"Error: Vector store loaded as None. Resetting.")
                    return
                
                # Load metadata with corruption fallback
                try:
                    with open(metadata_path, 'rb') as f:
                        self.metadata = pickle.load(f)
                except (pickle.UnpicklingError, EOFError):
                    print(f"Warning: Corrupted metadata file. Resetting metadata.")
                    self.metadata = {}
                
                print(f"Loaded existing vector database from {self.db_path}")
            except PermissionError:
                print(f"Error: Permission denied reading vector database. Creating new one.")
                self.vector_store = None
            except Exception as e:
                print(f"Error loading vector database: {e}. Creating new one.")
                self.vector_store = None
    
    def add_documents(self, documents: List[Dict], source: str):
        """
        Add documents to vector store
        
        Args:
            documents: List of dicts with 'content' and 'file_name' keys
            source: Source of documents (e.g., 'policies', 'effects')
        """
        if not documents:
            return
        
        if not isinstance(documents, (list, tuple)):
            print(f"Error: documents must be a list, got {type(documents)}")
            return
        
        if not source or not isinstance(source, str):
            print(f"Error: source must be a non-empty string")
            return
        
        # Filter out invalid documents and sanitize content
        texts = []
        metadatas = []
        max_content_length = 50000
        
        for idx, doc in enumerate(documents):
            if not isinstance(doc, dict):
                print(f"Warning: Document {idx} is not a dict, skipping")
                continue
            
            content = doc.get('content', '')
            if not content or not isinstance(content, str):
                print(f"Warning: Document {idx} has empty/invalid content, skipping")
                continue
            
            # Limit content length to prevent embedding issues
            if len(content) > max_content_length:
                content = content[:max_content_length]
            
            texts.append(content)
            metadatas.append({
                'source': str(source).lower(),
                'file_name': str(doc.get('file_name', 'unknown'))[:500],
                'page': int(doc.get('page', 0)) if isinstance(doc.get('page'), (int, float)) else 0
            })
        
        if not texts:
            print("Warning: No valid documents to add after filtering.")
            return
        
        try:
            if self.vector_store is None:
                # Create new vector store
                self.vector_store = FAISS.from_texts(
                    texts=texts,
                    embedding=self.embeddings,
                    metadatas=metadatas
                )
            else:
                # Add to existing vector store
                self.vector_store.add_texts(texts, metadatas=metadatas)
            
            # Update metadata
            from datetime import datetime
            self.metadata[str(source).lower()] = {
                'doc_count': len(texts),
                'updated_at': datetime.now().isoformat(),
                'file_names': [m.get('file_name', '') for m in metadatas]
            }
            
            print(f"Added {len(texts)} documents from {source}")
            
        except Exception as e:
            print(f"Error adding documents to vector store: {e}")
    
    def retrieve(self, query: str, k: int = 5, source: str = None) -> List[Tuple[str, float]]:
        """
        Retrieve relevant documents
        
        Args:
            query: Search query
            k: Number of results to return
            source: Filter by source (optional)
        
        Returns:
            List of (document_content, similarity_score) tuples
        """
        if self.vector_store is None:
            return []
        
        # Validate query
        if not query or not isinstance(query, str):
            return []
        
        query = query.strip()
        if not query:
            return []
        
        # Validate k
        try:
            k = int(k)
            if k < 1:
                k = 5
            if k > 100:
                k = 100
        except (ValueError, TypeError):
            k = 5
        
        try:
            if source and isinstance(source, str):
                # Search with source filter
                results = self.vector_store.similarity_search_with_score(
                    query, k=k, filter={"source": source.lower().strip()}
                )
            else:
                # Search all documents
                results = self.vector_store.similarity_search_with_score(query, k=k)
            
            return results if results else []
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []
    
    def save(self):
        """Save vector store to disk"""
        if self.vector_store is None:
            return
        
        try:
            self.vector_store.save_local(str(self.db_path))
            
            # Save metadata
            metadata_path = self.db_path / "metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            print(f"Vector database saved to {self.db_path}")
        except Exception as e:
            print(f"Error saving vector database: {e}")
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            'db_path': str(self.db_path),
            'metadata': self.metadata,
            'vector_store_ready': self.vector_store is not None
        }
    
    def clear(self):
        """Clear vector database"""
        import shutil
        if self.db_path.exists():
            shutil.rmtree(self.db_path)
        self.vector_store = None
        self.metadata = {}
        print(f"Vector database cleared from {self.db_path}")
