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
                self.vector_store = FAISS.load_local(
                    str(self.db_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"Loaded existing vector database from {self.db_path}")
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
        
        # Extract texts from documents
        texts = [doc.get('content', '') for doc in documents]
        metadatas = [
            {
                'source': source,
                'file_name': doc.get('file_name', 'unknown'),
                'page': doc.get('page', 0)
            }
            for doc in documents
        ]
        
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
            self.metadata[source] = {
                'doc_count': len(documents),
                'updated_at': datetime.now().isoformat(),
                'file_names': [doc.get('file_name', '') for doc in documents]
            }
            
            print(f"Added {len(documents)} documents from {source}")
            
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
        
        try:
            if source:
                # Search with source filter
                results = self.vector_store.similarity_search_with_score(
                    query, k=k, filter={"source": source}
                )
            else:
                # Search all documents
                results = self.vector_store.similarity_search_with_score(query, k=k)
            
            return results
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
