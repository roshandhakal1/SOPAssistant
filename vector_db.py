# Fix for Streamlit Cloud SQLite compatibility
import sys
import subprocess
import os

# Install and configure pysqlite3 for Streamlit Cloud
try:
    import pysqlite3
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Tuple
from pathlib import Path

class VectorDatabase:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        self.collection_name = "sop_documents"
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(name=self.collection_name)
        except:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_documents(self, documents: List[Dict], embeddings: List[List[float]]):
        ids = []
        metadatas = []
        texts = []
        
        for i, doc in enumerate(documents):
            doc_id = f"{doc['metadata']['source']}_{doc['metadata']['chunk_id']}"
            ids.append(doc_id)
            metadatas.append(doc['metadata'])
            texts.append(doc['content'])
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )
    
    def delete_document(self, file_path: str):
        try:
            results = self.collection.get(
                where={"source": file_path}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
        except Exception as e:
            print(f"Error deleting document {file_path}: {str(e)}")
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> Tuple[List[str], List[Dict]]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        
        return documents, metadatas
    
    def has_documents(self) -> bool:
        try:
            count = self.collection.count()
            return count > 0
        except:
            return False
    
    def get_collection_info(self) -> Dict:
        try:
            count = self.collection.count()
            unique_docs = self.get_unique_document_count()
            return {"count": count, "unique_documents": unique_docs}
        except:
            return {"count": 0, "unique_documents": 0}
    
    def get_unique_document_count(self) -> int:
        """Get count of unique documents (not chunks)"""
        try:
            # First check if collection exists and has data
            total_count = self.collection.count()
            if total_count == 0:
                return 0
            
            # Get all metadata to count unique sources
            results = self.collection.get(include=['metadatas'])
            if not results or not results.get('metadatas'):
                print("No metadata found in collection")
                return 0
            
            metadatas = results['metadatas']
            print(f"Total chunks found: {len(metadatas)}")
            
            # Debug: print first metadata entry
            if metadatas:
                print(f"Sample metadata keys: {list(metadatas[0].keys())}")
                print(f"Sample metadata: {metadatas[0]}")
            
            # Count unique source files using 'source' field (from document_processor.py)
            unique_sources = set()
            for metadata in metadatas:
                if 'source' in metadata and metadata['source']:
                    unique_sources.add(metadata['source'])
                elif 'filename' in metadata and metadata['filename']:
                    # Fallback to filename if source not available
                    unique_sources.add(metadata['filename'])
            
            print(f"Unique sources found: {len(unique_sources)}")
            if unique_sources:
                print(f"Sample sources: {list(unique_sources)[:3]}")
            
            return len(unique_sources)
        except Exception as e:
            print(f"Error counting unique documents: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
    
    def reset_database(self):
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
        except Exception as e:
            print(f"Error resetting database: {str(e)}")