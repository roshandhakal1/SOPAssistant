import streamlit as st
import os
from datetime import datetime
from pathlib import Path
import hashlib
import json

from document_processor import DocumentProcessor
from embeddings_manager import EmbeddingsManager
from vector_db import VectorDatabase
from rag_handler import RAGHandler
from config import Config
from expert_consultant import ManufacturingExpertConsultant
from session_document_handler import SessionDocumentHandler
from auth import require_auth
from chat_history_manager import ChatHistoryManager

st.set_page_config(page_title="Manufacturing Knowledge Assistant", page_icon="🏭", layout="wide")

# Require authentication before accessing the app
auth_manager = require_auth()

# Check if admin portal should be shown
if hasattr(st.session_state, 'show_admin_portal') and st.session_state.show_admin_portal:
    from user_manager import UserManager
    
    st.markdown("# 👤 Admin Portal")
    
    if st.button("🔙 Back to Main App", type="secondary"):
        st.session_state.show_admin_portal = False
        st.rerun()
    
    st.markdown("---")
    
    # Initialize user manager and render portal
    user_manager = UserManager()
    user_manager.render_admin_portal()
    st.stop()  # Stop here, don't render the main app

@st.cache_resource(ttl=3600)  # 1 hour cache
def initialize_components():
    config = Config()
    doc_processor = DocumentProcessor()
    embeddings_manager = EmbeddingsManager(config.GEMINI_API_KEY)
    vector_db = VectorDatabase(config.CHROMA_PERSIST_DIR)
    session_doc_handler = SessionDocumentHandler(embeddings_manager)
    chat_history_manager = ChatHistoryManager()
    return config, doc_processor, embeddings_manager, vector_db, session_doc_handler, chat_history_manager

def get_model_components(config, vector_db):
    """Get model-specific components based on user settings."""
    from user_manager import UserManager
    user_manager = UserManager()
    
    # Get current user's model preferences
    username = st.session_state.get('username', 'unknown')
    standard_model = user_manager.get_user_model(username, mode="standard")
    expert_model = user_manager.get_user_model(username, mode="expert")
    
    # Create model-specific handlers
    rag_handler = RAGHandler(config.GEMINI_API_KEY, vector_db, model_name=standard_model)
    expert_consultant = ManufacturingExpertConsultant(config.GEMINI_API_KEY, model_name=expert_model)
    
    return rag_handler, expert_consultant, standard_model, expert_model

def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_file_index():
    index_path = "file_index.json"
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return json.load(f)
    return {}

def save_file_index(index):
    with open("file_index.json", 'w') as f:
        json.dump(index, f)

def check_for_updates(config, doc_processor, embeddings_manager, vector_db):
    sop_folder = config.SOP_FOLDER
    current_index = load_file_index()
    new_index = {}
    updates = []
    
    for file_path in Path(sop_folder).glob("**/*"):
        if file_path.suffix.lower() in ['.pdf', '.docx', '.doc']:
            file_str = str(file_path)
            file_hash = get_file_hash(file_str)
            new_index[file_str] = file_hash
            
            if file_str not in current_index or current_index[file_str] != file_hash:
                updates.append(file_str)
    
    removed_files = set(current_index.keys()) - set(new_index.keys())
    
    return updates, removed_files, new_index

def process_updates(updates, removed_files, new_index, doc_processor, embeddings_manager, vector_db):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    if removed_files:
        status_text.text(f"Removing {len(removed_files)} deleted files from database...")
        for file_path in removed_files:
            vector_db.delete_document(file_path)
    
    if updates:
        total = len(updates)
        for i, file_path in enumerate(updates):
            progress_percent = (i + 1) / total
            status_text.text(f"Processing {i+1}/{total}: {os.path.basename(file_path)}")
            
            try:
                # Show sub-progress
                with st.expander(f"Processing {os.path.basename(file_path)}", expanded=False):
                    st.write("📄 Reading document...")
                    documents = doc_processor.process_file(file_path)
                    st.write(f"✂️ Split into {len(documents)} chunks")
                    
                    st.write("🧮 Creating embeddings...")
                    texts = [doc['content'] for doc in documents]
                    embeddings = embeddings_manager.create_embeddings(texts)
                    st.write(f"✅ Created {len(embeddings)} embeddings")
                    
                    st.write("💾 Storing in vector database...")
                    vector_db.add_documents(documents, embeddings)
                    st.write("✅ Stored successfully")
                
            except Exception as e:
                st.error(f"Error processing {file_path}: {str(e)}")
            
            progress_bar.progress(progress_percent)
    
    save_file_index(new_index)
    status_text.text("✅ Update complete!")
    
    # Show summary
    st.success(f"Processed {len(updates)} files successfully!")
    
    # Clear progress after 2 seconds
    import time
    time.sleep(2)
    progress_bar.empty()
    status_text.empty()

def main():
    # Import auth manager and render user info in header area
    from auth import AuthManager
    auth_manager = AuthManager()
    
    if auth_manager.is_session_valid():
        auth_manager.render_user_info()
    
    # Apple-inspired minimal luxury header
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&display=swap');
    
    /* SOP document reference styling */
    .sop-reference {
        color: #0066cc;
        background-color: rgba(0, 102, 204, 0.05);
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.875rem;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
        display: inline-block;
        margin: 2px 0;
        border: 1px solid rgba(0, 102, 204, 0.1);
        transition: all 0.2s ease;
    }
    
    .sop-reference:hover {
        background-color: rgba(0, 102, 204, 0.1);
        border-color: rgba(0, 102, 204, 0.2);
    }
    
    .uploaded-doc-reference {
        color: #34c759;
        background-color: rgba(52, 199, 89, 0.05);
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.875rem;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
        display: inline-block;
        margin: 2px 0;
        border: 1px solid rgba(52, 199, 89, 0.1);
    }
    
    /* Inline SOP references in response text */
    .sop-reference-inline {
        color: #0066cc;
        background-color: rgba(0, 102, 204, 0.05);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.875rem;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
        border: 1px solid rgba(0, 102, 204, 0.08);
        white-space: nowrap;
    }
    
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        margin: 0 0 1.5rem 0;
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Hide all Streamlit auto-generated anchor links */
    .main-header a,
    .main-header .anchor-link,
    .main-header [data-testid="stMarkdownContainer"] a {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Remove anchor pseudo-elements */
    .main-header h1::before,
    .main-header h1::after,
    .main-header h2::before,
    .main-header h2::after {
        display: none !important;
        content: none !important;
    }
    
    /* Ensure clean header layout */
    .main-header h1,
    .main-header h2,
    .main-header p {
        position: relative;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
    
    /* Override any Streamlit default spacing */
    .main-header * {
        text-decoration: none !important;
    }
    
    .main-title {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 2.75rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #1d1d1f 0%, #6e6e73 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .main-title:hover {
        transform: translateY(-2px);
        filter: brightness(1.1);
    }
    
    .sop-title {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 4.5rem;
        font-weight: 700;
        margin: 0 0 1rem 0;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #1d1d1f 0%, #6e6e73 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 0.9;
        animation: fadeInUp 0.8s ease-out forwards;
    }
    
    .subtitle {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 1.125rem;
        font-weight: 400;
        margin: 0.75rem 0 0 0;
        color: #86868b;
        letter-spacing: -0.01em;
        animation: fadeInUp 0.8s ease-out forwards;
    }
    
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    
    /* Fixed expert indicator for chat area */
    .expert-floating-indicator {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(52, 199, 89, 0.95);
        border: 1px solid rgba(52, 199, 89, 1);
        border-radius: 20px;
        font-family: 'SF Pro Display', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3);
        opacity: 1;
        transform: translateX(0) scale(1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: floatingPulse 3s ease-in-out infinite;
    }
    
    .expert-floating-indicator.entering {
        animation: slideInFromRight 0.6s ease-out forwards, floatingPulse 3s ease-in-out infinite 1s;
    }
    
    .expert-floating-indicator.exiting {
        opacity: 0;
        transform: translateX(100px) scale(0.8);
    }
    
    .expert-floating-dot {
        width: 6px;
        height: 6px;
        background: white;
        border-radius: 50%;
        animation: fastPulse 1.5s ease-in-out infinite;
    }
    
    @keyframes slideInFromRight {
        0% {
            opacity: 0;
            transform: translateX(100px) scale(0.8);
        }
        100% {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
    }
    
    @keyframes floatingPulse {
        0%, 100% { 
            transform: scale(1);
            box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3);
        }
        50% { 
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(52, 199, 89, 0.4);
        }
    }
    
    @keyframes fastPulse {
        0%, 100% { 
            opacity: 1;
            transform: scale(1); 
        }
        50% { 
            opacity: 0.7;
            transform: scale(0.8); 
        }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .main-title {
            background: linear-gradient(135deg, #f5f5f7 0%, #d2d2d7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            color: #a1a1a6;
        }
        .expert-indicator {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #f5f5f7;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Clean header without expert indicator
    expert_mode = st.session_state.get('mode') == 'expert_consultant'
    subtitle_text = "Advanced manufacturing expertise at your fingertips" if expert_mode else "Your knowledge companion for operational excellence"
    
    st.markdown(f"""
    <div class="main-header">
        <div class="sop-title">SOP Assistant</div>
        <div class="main-title">Manufacturing Intelligence Hub</div>
        <div class="subtitle">{subtitle_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    
    # Initialize session state for mode
    if 'mode' not in st.session_state:
        st.session_state.mode = 'standard'
    
    # Initialize with progress bar if first run
    if 'initialized' not in st.session_state:
        with st.spinner("Initializing components..."):
            components = initialize_components()
            st.session_state.components = components
            config, doc_processor, embeddings_manager, vector_db, session_doc_handler, chat_history_manager = components
            
            # Get model-specific components
            rag_handler, expert_consultant, standard_model, expert_model = get_model_components(config, vector_db)
            
            # Check if this is first run (no documents in DB)
            if not vector_db.has_documents():
                st.info("First time setup detected. Processing SOP documents...")
                updates, removed_files, new_index = check_for_updates(
                    config, doc_processor, embeddings_manager, vector_db
                )
                if updates:
                    process_updates(updates, removed_files, new_index, 
                                  doc_processor, embeddings_manager, vector_db)
            
            st.session_state.initialized = True
    else:
        # Use cached components if available
        if 'components' in st.session_state:
            config, doc_processor, embeddings_manager, vector_db, session_doc_handler, chat_history_manager = st.session_state.components
        else:
            components = initialize_components()
            st.session_state.components = components
            config, doc_processor, embeddings_manager, vector_db, session_doc_handler, chat_history_manager = components
        
        # Get model-specific components based on user settings
        rag_handler, expert_consultant, standard_model, expert_model = get_model_components(config, vector_db)
    
    with st.sidebar:
        st.header("⚙️ Assistant Mode")
        mode = st.radio(
            "Select mode:",
            ["Knowledge Search", "Expert Consultant"],
            index=0 if st.session_state.mode == 'standard' else 1,
            help="Knowledge Search: Quick SOP lookups\nExpert Consultant: Strategic manufacturing guidance",
            key="mode_selector"
        )
        # Update session state based on selection (only if changed)
        new_mode = 'standard' if mode == "Knowledge Search" else 'expert_consultant'
        if st.session_state.mode != new_mode:
            st.session_state.mode = new_mode
        
        # Only show expert details if in expert mode (cached)
        if st.session_state.mode == 'expert_consultant':
            st.success("🏭 Expert Mode Active")
            
            with st.expander("Expert Capabilities", expanded=False):
                st.markdown("""
                **Integrated Expertise:**
                - **CEO**: Strategic vision & growth
                - **CFO**: Financial optimization
                - **CMO**: Market intelligence
                - **Quality**: Compliance & standards
                - **Supply Chain**: Operations excellence
                """)
        
        st.divider()
        
        # Condensed Document Management
        with st.expander("📁 Document Management", expanded=False):
            st.caption(f"SOP Folder: {config.SOP_FOLDER}")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Check for Updates", type="secondary", use_container_width=True):
                    with st.spinner("Checking for updates..."):
                        updates, removed_files, new_index = check_for_updates(
                            config, doc_processor, embeddings_manager, vector_db
                        )
                        
                        if updates or removed_files:
                            st.success(f"Found {len(updates)} new/modified, {len(removed_files)} removed")
                            process_updates(updates, removed_files, new_index, 
                                          doc_processor, embeddings_manager, vector_db)
                        else:
                            st.info("All documents up to date")
            
            with col2:
                collection_info = vector_db.get_collection_info()
                unique_count = collection_info.get('unique_documents', 0)
                total_chunks = collection_info.get('count', 0)
                
                # Show unique count if available, otherwise show an estimate
                if unique_count > 0:
                    st.metric("Total SOPs", unique_count)
                elif total_chunks > 0:
                    # Rough estimate: assume average 6 chunks per document
                    estimated_docs = max(1, total_chunks // 6)
                    st.metric("Total SOPs", f"~{estimated_docs}")
                    st.caption(f"({total_chunks} chunks)")
                else:
                    st.metric("Total SOPs", 0)
        
        st.divider()
        
        # Chat Management Section
        st.header("💬 Chat Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Chat", type="secondary", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("📥 New Chat", type="secondary", use_container_width=True):
                # Save current chat to persistent history if it has messages
                if 'messages' in st.session_state and st.session_state.messages:
                    username = st.session_state.get('username', 'unknown')
                    chat_data = {
                        'messages': st.session_state.messages.copy(),
                        'mode': st.session_state.get('mode', 'standard')
                    }
                    chat_history_manager.save_chat(username, chat_data)
                
                # Clear current messages
                st.session_state.messages = []
                st.rerun()
        
        # Export chat button
        if st.session_state.get('messages'):
            if st.button("💾 Export Chat", type="secondary", use_container_width=True):
                chat_export = {
                    'timestamp': datetime.now().isoformat(),
                    'mode': st.session_state.get('mode', 'standard'),
                    'messages': st.session_state.messages
                }
                
                # Create download button for JSON export
                st.download_button(
                    label="📥 Download Chat as JSON",
                    data=json.dumps(chat_export, indent=2),
                    file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Show persistent chat history
        if hasattr(st.session_state, 'username'):
            username = st.session_state.username
            recent_chats = chat_history_manager.get_recent_chats(username, limit=5)
            
            if recent_chats:
                st.divider()
                st.subheader("📚 Chat History")
                
                for i, chat in enumerate(recent_chats):
                    chat_title = chat.get('title', 'Untitled Chat')
                    chat_date = chat.get('timestamp', '')[:16].replace('T', ' ')
                    mode_icon = "🤖" if chat.get('mode') == 'expert_consultant' else "📖"
                    
                    with st.expander(f"{mode_icon} {chat_date} - {chat_title}", expanded=False):
                        col_load, col_delete = st.columns([3, 1])
                        
                        with col_load:
                            if st.button("📂 Load Chat", key=f"load_chat_{i}"):
                                st.session_state.messages = chat['messages']
                                st.session_state.mode = chat['mode']
                                st.rerun()
                        
                        with col_delete:
                            if st.button("🗑️", key=f"delete_chat_{i}", help="Delete this chat"):
                                chat_history_manager.delete_chat(username, chat['id'])
                                st.rerun()
                
                # Clear all history option
                if st.button("🗑️ Clear All History", type="secondary", help="Delete all your chat history"):
                    chat_history_manager.clear_all_chats(username)
                    st.success("Chat history cleared!")
                    st.rerun()
        
        # Admin Portal (only show for admin users)
        if hasattr(st.session_state, 'user_role') and st.session_state.user_role == 'admin':
            st.divider()
            st.header("👤 Admin Portal")
            
            if st.button("🔧 Manage Users", type="primary", use_container_width=True):
                st.session_state.show_admin_portal = True
            
            st.caption("🔐 Administrator privileges detected")
        
    
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Check if message contains HTML and render accordingly
            content = message["content"]
            if '<span class="sop-reference-inline">' in content:
                st.markdown(content, unsafe_allow_html=True)
            else:
                st.markdown(content)
    
    # Document Upload Section
    with st.expander("📎 Upload Reference Documents", expanded=False):
        st.markdown("Upload documents to use as additional context for this conversation (PDF, DOCX, DOC)")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'doc'],
            help="Upload documents like templates, examples, or references to enhance responses"
        )
        
        # Initialize session documents
        if 'uploaded_documents' not in st.session_state:
            st.session_state.uploaded_documents = {}
        
        # Process uploaded files
        if uploaded_files:
            if st.button("🔄 Process Uploaded Documents"):
                with st.spinner("Processing uploaded documents..."):
                    processed_docs = session_doc_handler.process_uploaded_files(uploaded_files)
                    st.session_state.uploaded_documents.update(processed_docs)
                    st.success(f"Processed {len(processed_docs)} documents!")
        
        # Show uploaded documents summary
        if st.session_state.uploaded_documents:
            st.markdown("**Documents in this session:**")
            summary = session_doc_handler.get_document_summary(st.session_state.uploaded_documents)
            st.text(summary)
            
            if st.button("🗑️ Clear Uploaded Documents"):
                st.session_state.uploaded_documents = {}
                st.rerun()
    
    # Visual indicator for Expert Mode
    if st.session_state.mode == 'expert_consultant':
        st.info("🏭 **Expert Consultant Mode** | You have access to comprehensive manufacturing expertise across all business functions")
    
    # Show document context indicator
    if st.session_state.uploaded_documents:
        doc_count = len(st.session_state.uploaded_documents)
        st.success(f"📎 {doc_count} reference document{'s' if doc_count != 1 else ''} loaded for this conversation")
    
    # Update placeholder based on mode
    placeholder = "Ask about your SOPs..." if st.session_state.mode == 'standard' else "Ask for expert manufacturing advice..."
    
    if prompt := st.chat_input(placeholder):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if st.session_state.mode == 'standard':
                with st.spinner("Searching knowledge base..."):
                    # Get SOP results
                    response, sop_sources = rag_handler.query(prompt)
                    
                    # Check for uploaded documents
                    session_sources = []
                    if st.session_state.uploaded_documents:
                        query_embedding = rag_handler.embeddings_manager.create_query_embedding(prompt)
                        session_docs, session_metas = session_doc_handler.search_session_documents(
                            query_embedding, st.session_state.uploaded_documents, top_k=3
                        )
                        
                        if session_docs:
                            # Get SOP context for comparison
                            sop_embedding = rag_handler.embeddings_manager.create_query_embedding(prompt)
                            sop_docs, sop_metas = vector_db.search(sop_embedding, top_k=3)
                            
                            # Create combined context
                            combined_context = session_doc_handler.create_combined_context(
                                sop_docs, sop_metas, session_docs, session_metas
                            )
                            
                            # Generate enhanced response with session context
                            enhanced_prompt = f"""You are a helpful assistant that answers questions based on Standard Operating Procedures (SOPs) and uploaded reference documents.

{combined_context}

Question: {prompt}

Instructions:
1. Give priority to information from uploaded reference documents when relevant
2. Use SOPs as supporting context
3. Be specific and cite sources from both uploaded documents and SOPs
4. If creating materials, follow the format/style from uploaded reference documents
5. Structure your answer clearly with bullet points or numbered lists when appropriate

Answer:"""
                            
                            # Configure generation for maximum output
                            generation_config = {
                                "max_output_tokens": 8192,
                                "temperature": 0.1,
                                "top_p": 0.8,
                                "top_k": 40
                            }
                            
                            enhanced_response = rag_handler.model.generate_content(enhanced_prompt, generation_config=generation_config)
                            response = enhanced_response.text
                            session_sources = [meta['filename'] for meta in session_metas]
                    
                    st.markdown(response, unsafe_allow_html=True)
                    
                    # Show sources
                    if sop_sources or session_sources:
                        st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
                        if session_sources:
                            st.markdown("##### 📎 Referenced Uploaded Documents")
                            for source in session_sources:
                                st.markdown(f'<span class="uploaded-doc-reference">{source}</span>', unsafe_allow_html=True)
                        if sop_sources:
                            st.markdown("##### 📎 Referenced SOPs")
                            sop_html = " ".join([f'<span class="sop-reference">{source}</span>' for source in sop_sources])
                            st.markdown(sop_html, unsafe_allow_html=True)
            
            else:  # Expert Consultant mode
                with st.spinner("🏭 Manufacturing expert analyzing..."):
                    # Get relevant SOPs
                    query_embedding = rag_handler.embeddings_manager.create_query_embedding(prompt)
                    sop_documents, sop_metadatas = vector_db.search(query_embedding, top_k=5)
                    
                    # Include uploaded documents in expert analysis
                    session_documents = []
                    session_metadatas = []
                    if st.session_state.uploaded_documents:
                        session_documents, session_metadatas = session_doc_handler.search_session_documents(
                            query_embedding, st.session_state.uploaded_documents, top_k=3
                        )
                    
                    # Combine all context
                    all_context = []
                    if session_documents:
                        all_context.extend(session_documents)
                    if sop_documents:
                        all_context.extend(sop_documents)
                    
                    # Combine sources
                    sop_sources = list(set([meta['filename'] for meta in sop_metadatas])) if sop_metadatas else []
                    session_sources = [meta['filename'] for meta in session_metadatas] if session_metadatas else []
                    
                    # Analyze query
                    analysis = expert_consultant.analyze_query(prompt, all_context)
                    
                    # Generate expert response
                    expert_response = expert_consultant.generate_expert_response(prompt, all_context, analysis)
                    
                    # Display expert response with structured format
                    st.markdown("#### 🏭 Manufacturing Expert Analysis")
                    st.markdown(expert_response['main_response'], unsafe_allow_html=True)
                    
                    # Show expertise perspectives
                    if expert_response.get('expertise_perspectives'):
                        with st.expander("👥 Multi-Role Perspectives", expanded=True):
                            for role, perspective in expert_response['expertise_perspectives'].items():
                                st.markdown(f"**{role}**: {perspective}")
                    
                    # Show recommendations
                    if expert_response.get('recommendations'):
                        with st.expander("📋 Recommendations", expanded=True):
                            recs = expert_response['recommendations']
                            if recs.get('immediate'):
                                st.markdown("**Immediate Actions:**")
                                for rec in recs['immediate']:
                                    st.markdown(f"• {rec}")
                            if recs.get('short_term'):
                                st.markdown("**Short-term (3-6 months):**")
                                for rec in recs['short_term']:
                                    st.markdown(f"• {rec}")
                            if recs.get('long_term'):
                                st.markdown("**Long-term (6+ months):**")
                                for rec in recs['long_term']:
                                    st.markdown(f"• {rec}")
                    
                    # Show risks
                    if expert_response.get('risks_and_considerations'):
                        with st.expander("⚠️ Risks & Considerations"):
                            for risk in expert_response['risks_and_considerations']:
                                st.markdown(f"• {risk}")
                    
                    # Show confidence level
                    confidence = expert_response.get('confidence_level', 'medium')
                    confidence_color = {'high': 'green', 'medium': 'orange', 'low': 'red'}.get(confidence, 'gray')
                    st.markdown(f"**Confidence Level:** :{confidence_color}[{confidence.upper()}]")
                    
                    # Show follow-up questions
                    if expert_response.get('follow_up_questions'):
                        st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
                        st.markdown("**💭 Follow-up questions to consider:**")
                        for q in expert_response['follow_up_questions']:
                            st.markdown(f"• {q}")
                    
                    # Show all referenced sources
                    if sop_sources or session_sources:
                        st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
                        if session_sources:
                            st.markdown("##### 📎 Referenced Uploaded Documents")
                            for source in session_sources:
                                st.markdown(f'<span class="uploaded-doc-reference">{source}</span>', unsafe_allow_html=True)
                        if sop_sources:
                            st.markdown("##### 📎 Referenced SOPs")
                            sop_html = " ".join([f'<span class="sop-reference">{source}</span>' for source in sop_sources])
                            st.markdown(sop_html, unsafe_allow_html=True)
                    
                    response = expert_response['main_response']
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    if not vector_db.has_documents():
        st.warning("⚠️ No documents found in the vector database. Click 'Check for Updates' to process your SOP documents.")
    

if __name__ == "__main__":
    main()