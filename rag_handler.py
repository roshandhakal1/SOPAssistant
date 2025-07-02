import google.generativeai as genai
from typing import List, Tuple, Dict
from embeddings_manager import EmbeddingsManager
from abbreviation_mapper import AbbreviationMapper
import numpy as np

class RAGHandler:
    def __init__(self, api_key: str, vector_db, model_name: str = 'gemini-1.5-flash'):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.vector_db = vector_db
        self.embeddings_manager = EmbeddingsManager(api_key)
        self.top_k = 50  # Maximum comprehensive SOP coverage for 1500+ documents
        self.abbreviation_mapper = AbbreviationMapper()
        self.model_name = model_name
    
    def query(self, question: str, top_k: int = None) -> Tuple[str, List[str]]:
        # Special handling for document count queries
        if any(phrase in question.lower() for phrase in ["how many sop", "count sop", "number of sop", "total sop"]):
            try:
                # Get actual count from vector database
                collection_info = self.vector_db.get_collection_info()
                unique_docs = collection_info.get('unique_documents', 0)
                total_chunks = collection_info.get('count', 0)
                
                # Get unique Google Drive documents
                gdrive_count = 0
                try:
                    results = self.vector_db.collection.get(include=['metadatas'])
                    if results and results.get('metadatas'):
                        gdrive_docs = set()
                        for metadata in results['metadatas']:
                            if 'gdrive_id' in metadata:
                                gdrive_docs.add(metadata['gdrive_id'])
                        gdrive_count = len(gdrive_docs)
                except:
                    pass
                
                response = f"""## 📊 SOP Database Statistics

**Total Unique SOPs**: {max(unique_docs, gdrive_count)} documents

**Details**:
• **Processed Documents**: {unique_docs} fully indexed SOPs
• **Google Drive References**: {gdrive_count} linked documents
• **Total Data Chunks**: {total_chunks} searchable segments

**Note**: The knowledge base contains both fully processed documents and Google Drive references for comprehensive coverage of your SOP library."""
                
                return response, []
            except Exception as e:
                pass
        if top_k is None:
            top_k = self.top_k
        
        # Get expanded query variations
        query_variations = self.abbreviation_mapper.expand_query(question)
        
        # Collect results from all query variations
        all_documents = []
        all_metadatas = []
        seen_ids = set()  # Track unique documents
        
        for query_variant in query_variations[:8]:  # Maximum query variations for comprehensive coverage
            query_embedding = self.embeddings_manager.create_query_embedding(query_variant)
            # Search with increased results per variation to get comprehensive coverage
            documents, metadatas = self.vector_db.search(query_embedding, top_k=min(top_k * 3, 100))
            
            # Add unique results
            for doc, meta in zip(documents, metadatas):
                doc_id = meta.get('id', doc[:50])  # Use ID or first 50 chars as identifier
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
                    all_metadatas.append(meta)
        
        # If no results from expanded queries, try original query with higher results
        if not all_documents:
            query_embedding = self.embeddings_manager.create_query_embedding(question)
            all_documents, all_metadatas = self.vector_db.search(query_embedding, top_k=min(top_k * 3, 100))
        
        if not all_documents:
            return "I couldn't find any relevant information in the SOPs to answer your question. Try using full terms instead of abbreviations (e.g., 'accounts payable' instead of 'AP').", []
        
        # For maximum comprehensive search, use as many results as possible within token limits
        # Allow up to 4x the top_k to capture maximum relevant documents from all query variations
        # With 1500+ SOPs, aim for 100-200 document chunks for truly comprehensive answers
        max_results = min(len(all_documents), top_k * 4, 200)  # Cap at 200 for performance
        documents = all_documents[:max_results]
        metadatas = all_metadatas[:max_results]
        
        context = self._format_context(documents, metadatas)
        
        # Include query expansion info in prompt if abbreviation was expanded
        expansion_note = ""
        if len(query_variations) > 1:
            expansion_note = f"\nNote: Searched for variations including: {', '.join(query_variations[:3])}"
        
        prompt = f"""You are a friendly business advisor helping stakeholders understand their operations.{expansion_note}

I've reviewed {len(documents)} relevant documents from your knowledge base to answer your question.

RELEVANT INFORMATION FROM YOUR SOPS:
{context}

QUESTION: {question}

Please provide a clear, stakeholder-friendly response that:
- Uses the SPECIFIC information from the SOPs above to give a comprehensive answer
- Translates technical procedures into business value and impact
- Includes specific activities like CAPA, NCAs, production testing, audits, etc.
- Organizes the wide range of activities into logical groups
- Shows the business impact of each area
- Uses conversational language while being thorough and specific

Think of this as briefing an executive on what their QA department actually does day-to-day, using real information from your procedures.

Format your response naturally with:
- Clear headings for main activity areas
- Specific examples and processes from the SOPs
- Business impact of each function
- Comprehensive coverage of all major activities
- DO NOT include SOP document names in your response (they'll be listed separately)
- Focus on WHAT they do and WHY it matters, not WHICH documents describe it

CONVERSATIONAL, STAKEHOLDER-FRIENDLY ANSWER:"""
        
        # Configure generation with maximum output tokens
        generation_config = {
            "max_output_tokens": 8192,  # Maximum allowed for Gemini
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40
        }
        
        response = self.model.generate_content(prompt, generation_config=generation_config)
        answer = response.text
        
        # Clean up SOP names and track which ones were referenced
        import re
        sop_pattern = r'\b([A-Za-z0-9\-\_\(\)\s]+(?:Rev\d+(?:Draft\d+)?)?[A-Za-z0-9\-\_\(\)\s]*\.(doc|docx|pdf))\b'
        
        # Find all SOP names that were mentioned in the original response
        referenced_sops = set()
        sop_matches = re.findall(sop_pattern, answer)
        for match in sop_matches:
            if isinstance(match, tuple):
                referenced_sops.add(match[0])  # Full filename
            else:
                referenced_sops.add(match)
        
        # Remove SOP filenames from the response text for cleaner stakeholder presentation
        formatted_answer = re.sub(sop_pattern, '[document reference removed]', answer)
        
        # Clean up any leftover HTML spans
        formatted_answer = re.sub(r'<span class="sop-reference-inline">([^<]+)</span>', r'\1', formatted_answer)
        
        # Clean up artifacts from removal
        formatted_answer = re.sub(r'\[document reference removed\]\s*and\s*\[document reference removed\]', 'our procedures', formatted_answer)
        formatted_answer = re.sub(r'\[document reference removed\]', 'our procedures', formatted_answer)
        
        # Only return sources that were actually referenced OR the top 5 most relevant
        sources_with_metadata = []
        seen_files = set()
        
        # First, add sources that were explicitly referenced in the response
        for meta in metadatas:
            filename = meta['filename']
            if filename not in seen_files:
                # Check if this file was mentioned in the response
                if any(ref in filename for ref in referenced_sops):
                    seen_files.add(filename)
                    source_info = {'filename': filename}
                    if 'gdrive_link' in meta:
                        source_info['gdrive_link'] = meta['gdrive_link']
                    sources_with_metadata.append(source_info)
        
        # If no explicit references found or very few, add top relevant sources
        if len(sources_with_metadata) < 3:
            for meta in metadatas[:5]:  # Top 5 most relevant
                filename = meta['filename']
                if filename not in seen_files:
                    seen_files.add(filename)
                    source_info = {'filename': filename}
                    if 'gdrive_link' in meta:
                        source_info['gdrive_link'] = meta['gdrive_link']
                    sources_with_metadata.append(source_info)
                    if len(sources_with_metadata) >= 5:
                        break
        
        return formatted_answer, sources_with_metadata
    
    def _format_context(self, documents: List[str], metadatas: List[Dict]) -> str:
        context_parts = []
        
        for doc, meta in zip(documents, metadatas):
            context_parts.append(f"**From {meta['filename']}:**\n{doc}\n")
        
        return "\n---\n".join(context_parts)