"""
Session Document Handler for temporary document uploads
Processes documents uploaded during chat sessions
"""

import tempfile
import os
from typing import List, Dict, Optional
from document_processor import DocumentProcessor
from embeddings_manager import EmbeddingsManager
import streamlit as st

class SessionDocumentHandler:
    """Handles temporary document uploads for chat sessions."""
    
    def __init__(self, embeddings_manager: EmbeddingsManager):
        self.embeddings_manager = embeddings_manager
        self.document_processor = DocumentProcessor()
        self.session_documents = {}  # Store processed documents by session
        
    def process_uploaded_files(self, uploaded_files) -> Dict[str, any]:
        """
        Process uploaded files and return processed content.
        
        Returns:
            Dict containing processed documents and their embeddings
        """
        if not uploaded_files:
            return {}
            
        processed_docs = {}
        
        for uploaded_file in uploaded_files:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Process the document
                documents = self.document_processor.process_file(tmp_path)
                
                # Create embeddings
                texts = [doc['content'] for doc in documents]
                embeddings = self.embeddings_manager.create_embeddings(texts)
                
                processed_docs[uploaded_file.name] = {
                    'documents': documents,
                    'embeddings': embeddings,
                    'filename': uploaded_file.name,
                    'size': uploaded_file.size,
                    'type': uploaded_file.type
                }
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                processed_docs[uploaded_file.name] = {
                    'error': str(e),
                    'filename': uploaded_file.name
                }
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        return processed_docs
    
    def search_session_documents(self, query_embedding, uploaded_docs: Dict, top_k: int = 3) -> tuple:
        """
        Search through uploaded session documents.
        
        Returns:
            Tuple of (documents, metadatas) matching the query
        """
        all_documents = []
        all_metadatas = []
        all_embeddings = []
        
        # Collect all documents and embeddings from uploaded files
        for filename, doc_data in uploaded_docs.items():
            if 'error' in doc_data:
                continue
                
            documents = doc_data['documents']
            embeddings = doc_data['embeddings']
            
            for doc, embedding in zip(documents, embeddings):
                all_documents.append(doc['content'])
                all_embeddings.append(embedding)
                all_metadatas.append({
                    'filename': f"📎 {filename}",
                    'source': 'session_upload',
                    'page': doc.get('page', 1),
                    'chunk_id': doc.get('chunk_id', 0)
                })
        
        if not all_embeddings:
            return [], []
        
        # Calculate similarity scores
        import numpy as np
        similarities = []
        for embedding in all_embeddings:
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append(similarity)
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        top_documents = [all_documents[i] for i in top_indices]
        top_metadatas = [all_metadatas[i] for i in top_indices]
        
        return top_documents, top_metadatas
    
    def get_document_summary(self, uploaded_docs: Dict) -> str:
        """Get a summary of uploaded documents."""
        if not uploaded_docs:
            return "No documents uploaded in this session."
        
        summary = []
        for filename, doc_data in uploaded_docs.items():
            if 'error' in doc_data:
                summary.append(f"❌ {filename} - Error: {doc_data['error']}")
            else:
                chunk_count = len(doc_data['documents'])
                size_kb = doc_data['size'] // 1024
                summary.append(f"✅ {filename} - {chunk_count} chunks, {size_kb}KB")
        
        return "\n".join(summary)
    
    def create_combined_context(self, sop_documents: List[str], sop_metadatas: List[Dict],
                              session_documents: List[str], session_metadatas: List[Dict]) -> str:
        """
        Create combined context from both SOP database and session uploads.
        """
        context_parts = []
        
        # Add session documents first (higher priority)
        if session_documents:
            context_parts.append("**UPLOADED REFERENCE DOCUMENTS:**")
            for doc, meta in zip(session_documents, session_metadatas):
                context_parts.append(f"**From {meta['filename']}:**\n{doc}\n")
            context_parts.append("---")
        
        # Add SOP documents
        if sop_documents:
            context_parts.append("**EXISTING SOPs:**")
            for doc, meta in zip(sop_documents, sop_metadatas):
                context_parts.append(f"**From {meta['filename']}:**\n{doc}\n")
        
        return "\n".join(context_parts)