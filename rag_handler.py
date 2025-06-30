import google.generativeai as genai
from typing import List, Tuple, Dict
from embeddings_manager import EmbeddingsManager
from abbreviation_mapper import AbbreviationMapper
import numpy as np

class RAGHandler:
    def __init__(self, api_key: str, vector_db):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.vector_db = vector_db
        self.embeddings_manager = EmbeddingsManager(api_key)
        self.top_k = 5
        self.abbreviation_mapper = AbbreviationMapper()
    
    def query(self, question: str, top_k: int = None) -> Tuple[str, List[str]]:
        if top_k is None:
            top_k = self.top_k
        
        # Get expanded query variations
        query_variations = self.abbreviation_mapper.expand_query(question)
        
        # Collect results from all query variations
        all_documents = []
        all_metadatas = []
        seen_ids = set()  # Track unique documents
        
        for query_variant in query_variations[:3]:  # Limit to top 3 variations to avoid too many searches
            query_embedding = self.embeddings_manager.create_query_embedding(query_variant)
            documents, metadatas = self.vector_db.search(query_embedding, top_k=top_k)
            
            # Add unique results
            for doc, meta in zip(documents, metadatas):
                doc_id = meta.get('id', doc[:50])  # Use ID or first 50 chars as identifier
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
                    all_metadatas.append(meta)
        
        # If no results from expanded queries, try original query
        if not all_documents:
            query_embedding = self.embeddings_manager.create_query_embedding(question)
            all_documents, all_metadatas = self.vector_db.search(query_embedding, top_k=top_k)
        
        if not all_documents:
            return "I couldn't find any relevant information in the SOPs to answer your question. Try using full terms instead of abbreviations (e.g., 'accounts payable' instead of 'AP').", []
        
        # Limit to top k results
        documents = all_documents[:top_k]
        metadatas = all_metadatas[:top_k]
        
        context = self._format_context(documents, metadatas)
        
        # Include query expansion info in prompt if abbreviation was expanded
        expansion_note = ""
        if len(query_variations) > 1:
            expansion_note = f"\nNote: Searched for variations including: {', '.join(query_variations[:3])}"
        
        prompt = f"""You are a helpful assistant that answers questions based on Standard Operating Procedures (SOPs).{expansion_note}

Context from SOPs:
{context}

Question: {question}

Instructions:
1. Answer the question based ONLY on the provided SOP context
2. Be specific and cite the relevant SOP titles when referencing information
3. If the context doesn't contain enough information to fully answer the question, say so
4. Structure your answer clearly with bullet points or numbered lists when appropriate
5. For questions about processes or lifecycles, list the steps in order

Answer:"""
        
        response = self.model.generate_content(prompt)
        answer = response.text
        
        sources = list(set([meta['filename'] for meta in metadatas]))
        
        return answer, sources
    
    def _format_context(self, documents: List[str], metadatas: List[Dict]) -> str:
        context_parts = []
        
        for doc, meta in zip(documents, metadatas):
            context_parts.append(f"**From {meta['filename']}:**\n{doc}\n")
        
        return "\n---\n".join(context_parts)