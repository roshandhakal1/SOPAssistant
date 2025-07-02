# Fix for Streamlit Cloud SQLite compatibility
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

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
from multi_expert_system import MultiExpertSystem
# Session document handler removed - all document management in Admin Portal
from auth import require_auth
from chat_history_manager import ChatHistoryManager
from cloud_storage import CloudStorageUI

st.set_page_config(page_title="Manufacturing Knowledge Assistant", page_icon="🏭", layout="wide")

# Force deployment update - v2024.1

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
    chat_history_manager = ChatHistoryManager()
    return config, doc_processor, embeddings_manager, vector_db, chat_history_manager

def handle_unified_chat_input(multi_expert_system):
    """Enhanced chat input with expert selection dropdown"""
    
    # Get available experts
    available_experts = multi_expert_system.get_available_experts()
    
    # Expert selection above chat input - clean and visible
    col1, col2 = st.columns([2, 1])
    
    with col1:
        expert_options = ["💬 General Search (All SOPs)"]
        expert_map = {"💬 General Search (All SOPs)": ""}
        
        for expert_name, expert_info in available_experts.items():
            clean_name = expert_name.replace("Expert", "")
            display_text = f"🎯 {clean_name} - {expert_info['title']}"
            expert_options.append(display_text)
            expert_map[display_text] = f"@{expert_name}"
        
        selected_expert = st.selectbox(
            "Choose consultation type:",
            expert_options,
            key="expert_selector",
            help="Select how you want your question answered"
        )
    
    with col2:
        # Show selected expert info
        expert_mention = expert_map.get(selected_expert, "")
        if expert_mention:
            st.markdown(f"**Selected:** {expert_mention}")
        else:
            st.markdown("**Mode:** General search")
    
    # Main chat input
    user_question = st.chat_input(
        "Ask your question...",
        key="main_chat_input"
    )
    
    # Combine question with expert mention if one is selected
    if user_question:
        if expert_mention:
            return f"{expert_mention} {user_question}"
        else:
            return user_question
    
    return None

def handle_expert_chat_input_deprecated(multi_expert_system):
    """Handle chat input with expert autocomplete functionality"""
    
    # Initialize session state for expert input
    if 'expert_input_key' not in st.session_state:
        st.session_state.expert_input_key = 0
    
    # Expert selection interface
    st.markdown("### 💬 Ask the Experts")
    
    # Quick expert selection buttons (always visible)
    available_experts = multi_expert_system.get_available_experts()
    
    with st.expander("🎯 Quick Expert Selection", expanded=False):
        st.markdown("**Click an expert to add them to your question:**")
        
        # Create a 3-column layout for expert buttons
        expert_list = list(available_experts.items())
        for i in range(0, len(expert_list), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(expert_list):
                    expert_name, expert_info = expert_list[i + j]
                    with col:
                        if st.button(
                            f"{expert_info['mention']}\n{expert_info['title'][:25]}...",
                            key=f"quick_expert_{expert_name}_{i}_{j}",
                            help=f"Specializes in: {', '.join(expert_info['specializations'])}",
                            use_container_width=True
                        ):
                            # Add this expert to the input
                            current_text = st.session_state.get('current_expert_input', '')
                            if f"@{expert_name}" not in current_text:
                                new_text = f"@{expert_name} {current_text}".strip()
                                st.session_state.current_expert_input = new_text
                                st.session_state.expert_input_key += 1
                                st.rerun()
    
    # Main text input with chat-like interface
    user_input = st.text_area(
        "Your question:",
        value=st.session_state.get('current_expert_input', ''),
        placeholder="Type your question here... Use @ to mention specific experts (e.g., @QualityExpert @ManufacturingExpert how do we improve our process?)",
        height=100,
        key=f"expert_chat_textarea_{st.session_state.expert_input_key}"
    )
    
    # Update session state
    st.session_state.current_expert_input = user_input
    
    # Show expert suggestions when @ is typed
    if "@" in user_input:
        # Find all @ mentions
        import re
        at_positions = [m.start() for m in re.finditer(r'@', user_input)]
        
        if at_positions:
            last_at_pos = at_positions[-1]
            # Get text after the last @
            text_after_last_at = user_input[last_at_pos + 1:].split()[0] if last_at_pos + 1 < len(user_input) else ""
            
            # Show suggestions for incomplete mentions
            if not text_after_last_at or not text_after_last_at.endswith((' ', '\n')):
                with st.container():
                    st.markdown("**💡 Expert Suggestions:**")
                    
                    # Filter experts based on partial typing
                    matching_experts = []
                    for expert_name, expert_info in available_experts.items():
                        if text_after_last_at.lower() in expert_name.lower():
                            matching_experts.append((expert_name, expert_info))
                    
                    if matching_experts:
                        # Show top 6 matching experts in 2 rows of 3
                        for i in range(0, min(6, len(matching_experts)), 3):
                            cols = st.columns(3)
                            for j, col in enumerate(cols):
                                if i + j < len(matching_experts):
                                    expert_name, expert_info = matching_experts[i + j]
                                    with col:
                                        if st.button(
                                            f"@{expert_name}",
                                            key=f"suggest_expert_{expert_name}_{i}_{j}",
                                            help=f"{expert_info['title']} - {', '.join(expert_info['specializations'][:2])}",
                                            use_container_width=True
                                        ):
                                            # Replace the incomplete mention
                                            before_at = user_input[:last_at_pos]
                                            after_mention = user_input[last_at_pos + 1 + len(text_after_last_at):]
                                            new_text = f"{before_at}@{expert_name} {after_mention}".strip()
                                            st.session_state.current_expert_input = new_text
                                            st.session_state.expert_input_key += 1
                                            st.rerun()
    
    # Send button and actions
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Show mentioned experts
        mentioned_experts = []
        if user_input:
            import re
            mentions = re.findall(r'@(\w+)', user_input)
            for mention in mentions:
                for expert_name in available_experts.keys():
                    if mention.lower() == expert_name.lower() or mention.lower() in expert_name.lower():
                        if expert_name not in mentioned_experts:
                            mentioned_experts.append(expert_name)
                        break
        
        if mentioned_experts:
            expert_names = [multi_expert_system.experts[name].name for name in mentioned_experts]
            st.info(f"📋 **Consulting:** {', '.join(expert_names)}")
    
    with col2:
        clear_clicked = st.button("🗑️ Clear", help="Clear the input", use_container_width=True)
    
    with col3:
        send_clicked = st.button("🚀 Send", type="primary", use_container_width=True)
    
    # Handle actions
    if clear_clicked:
        st.session_state.current_expert_input = ""
        st.session_state.expert_input_key += 1
        st.rerun()
    
    if send_clicked and user_input.strip():
        final_prompt = user_input.strip()
        # Clear the input
        st.session_state.current_expert_input = ""
        st.session_state.expert_input_key += 1
        return final_prompt
    
    return None

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
    multi_expert_system = MultiExpertSystem(config.GEMINI_API_KEY, model_name=expert_model)
    
    return rag_handler, multi_expert_system, standard_model, expert_model

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
        # Skip metadata files
        if file_path.suffix.lower() == '.gdrive_metadata':
            continue
            
        if file_path.suffix.lower() in ['.pdf', '.docx', '.doc', '.csv', '.md']:
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
    
    # Minimalist header - Apple style
    st.markdown("""
    <div class="main-header">
        <div class="main-title">Manufacturing Knowledge Assistant</div>
        <div class="subtitle">Ask questions. Get answers. Work smarter.</div>
    </div>
    """, unsafe_allow_html=True)
    
    
    # Initialize session state for mode
    if 'mode' not in st.session_state:
        st.session_state.mode = 'standard'
    
    # Initialize with progress bar if first run
    if 'initialized' not in st.session_state:
        try:
            with st.spinner("Initializing components..."):
                components = initialize_components()
                st.session_state.components = components
                config, doc_processor, embeddings_manager, vector_db, chat_history_manager = components
        except Exception as e:
            st.error(f"⚠️ Initialization error: {str(e)}")
            st.info("💡 Try refreshing the page or contact admin if the issue persists.")
            st.stop()
        
        # Get model-specific components
        rag_handler, expert_consultant, standard_model, expert_model = get_model_components(config, vector_db)
        
        # Auto-processing check for new files (if enabled)
        if st.session_state.get('auto_processing_enabled', False):
            try:
                with st.spinner("🔄 Checking for new files..."):
                    # Check for updates and auto-process
                    updates, removed_files, new_index = check_for_updates(
                        config, doc_processor, embeddings_manager, vector_db
                    )
                    
                    if updates:
                        with st.spinner(f"🔄 Auto-processing {len(updates)} new files..."):
                            process_updates(updates, removed_files, new_index, 
                                          doc_processor, embeddings_manager, vector_db)
                        st.success(f"✅ Auto-processed {len(updates)} new files!", icon="🤖")
            except Exception as e:
                st.warning(f"Auto-processing check failed: {str(e)}")
        
        # Check if knowledge base is empty (non-blocking)
        try:
            has_docs = vector_db.has_documents()
            if not has_docs:
                st.info("📊 Knowledge base is empty. App is ready - use Admin Portal to sync documents.")
                st.caption("💡 Admin can sync from Google Drive in Admin Portal → Integration tab")
        except Exception as e:
            st.warning("⚠️ Could not check knowledge base status. App is still functional.")
            st.caption(f"Debug: {str(e)}")
        
        st.session_state.initialized = True
    else:
        # Use cached components if available
        if 'components' in st.session_state:
            config, doc_processor, embeddings_manager, vector_db, chat_history_manager = st.session_state.components
        else:
            components = initialize_components()
            st.session_state.components = components
            config, doc_processor, embeddings_manager, vector_db, chat_history_manager = components
        
    
    # Get model-specific components based on user settings (after component initialization)
    rag_handler, multi_expert_system, standard_model, expert_model = get_model_components(config, vector_db)
    
    with st.sidebar:
        st.markdown("### 🏭 Knowledge Assistant")
        
        # Simple help section
        with st.expander("💡 Quick Tips", expanded=False):
            st.markdown("""
            **Expert Mentions:**
            Type `@` followed by expert name
            
            **Examples:**
            • `@Quality` - Quality & compliance
            • `@Manufacturing` - Production issues  
            • `@Safety` - Safety protocols
            
            **Pro tip:** Ask normally for SOP search
            """)
        
        # Usage stats (if helpful)
        with st.expander("📊 Session Info", expanded=False):
            # Show basic session stats
            username = st.session_state.get('username', 'Unknown')
            login_time = st.session_state.get('login_time')
            
            st.markdown(f"**User:** {username}")
            if login_time:
                st.markdown(f"**Session:** {login_time.strftime('%H:%M')}")
            
            # Document count
            try:
                doc_count = vector_db.collection.count() if hasattr(vector_db, 'collection') else 0
                st.markdown(f"**Knowledge Base:** {doc_count} documents")
            except:
                st.markdown("**Knowledge Base:** Connected")
        
        st.divider()
        
        # Knowledge Base Status (read-only for users)
        with st.expander("📊 Knowledge Base", expanded=False):
            try:
                collection_info = vector_db.get_collection_info()
                total_chunks = collection_info.get('count', 0)
                unique_docs = collection_info.get('unique_documents', 0)
                
                # Count Google Drive references
                gdrive_count = 0
                try:
                    results = vector_db.collection.get(include=['metadatas'], limit=10000)
                    if results and results.get('metadatas'):
                        gdrive_docs = set()
                        for metadata in results['metadatas']:
                            if 'gdrive_id' in metadata:
                                gdrive_docs.add(metadata['gdrive_id'])
                        gdrive_count = len(gdrive_docs)
                except:
                    pass
                
                # Show the higher count (either processed docs or gdrive refs)
                total_sops = max(unique_docs, gdrive_count)
                
                if total_sops > 0:
                    st.metric("📄 Total SOPs", f"{total_sops}")
                    if gdrive_count > unique_docs:
                        st.caption(f"🔗 {gdrive_count} Google Drive refs")
                    st.success("✅ Knowledge base is ready")
                else:
                    st.metric("📄 Documents", "0")
                    st.info("💡 Admin can sync documents in Admin Portal")
            except:
                st.warning("⚠️ Knowledge base connection issue")
            
            # Google Drive connection status (read-only)
            from cloud_storage import GoogleDriveManager
            gdrive = GoogleDriveManager()
            
            if gdrive.load_saved_credentials():
                st.caption("🔗 Google Drive: Connected")
            else:
                st.caption("🔗 Google Drive: Not connected")
        
        st.divider()
        
        # Simplified Chat Controls
        with st.expander("💬 Chat Controls", expanded=False):
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
            
            # Export option if chat has messages
            if st.session_state.get('messages'):
                st.divider()
                if st.button("💾 Export Chat", use_container_width=True):
                    chat_export = {
                        'timestamp': datetime.now().isoformat(),
                        'messages': st.session_state.messages
                    }
                    
                    # Create download button for JSON export
                    st.download_button(
                        label="📥 Download JSON",
                        data=json.dumps(chat_export, indent=2),
                        file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
        
        # Admin Portal Access (only for admin users)
        if hasattr(st.session_state, 'user_role') and st.session_state.user_role == 'admin':
            st.divider()
            
            if st.button("🔧 Admin Portal", type="primary", use_container_width=True):
                st.session_state.show_admin_portal = True
                st.rerun()
            
            st.caption("🔐 Admin access available")
        
    
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Apple-style clean welcome when no messages
    if not st.session_state.messages:
        st.markdown("## Welcome to your Knowledge Assistant")
        st.markdown("")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **🔍 Search SOPs**  
            Just ask your question naturally
            
            **💬 Expert Consultation**  
            Type @ to mention an expert
            """)
        
        with col2:
            st.markdown("""
            **📊 1,506 SOPs Available**  
            Comprehensive coverage
            
            **⚡ Fast & Accurate**  
            Enhanced search system
            """)
        
        st.markdown("")
        st.markdown("---")
        st.markdown("")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Check if message contains HTML and render accordingly
            content = message["content"]
            if '<span class="sop-reference-inline">' in content:
                st.markdown(content, unsafe_allow_html=True)
            else:
                st.markdown(content)
    
    # Clean interface - all document management moved to Admin Portal
    
    # Unified chat input with smart @mention detection
    prompt = handle_unified_chat_input(multi_expert_system)
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            # Check if the prompt contains @mentions for expert consultation
            mentioned_experts = multi_expert_system.parse_mentions(prompt)
            
            if mentioned_experts:
                # Expert consultation with full conversation context
                with st.spinner("🏭 Consulting experts..."):
                    # Get relevant SOPs and context
                    query_embedding = rag_handler.embeddings_manager.create_query_embedding(prompt)
                    sop_documents, sop_metadatas = vector_db.search(query_embedding, top_k=5)
                    
                    # Use SOP documents as context for expert consultation
                    all_context = []
                    if sop_documents:
                        all_context.extend(sop_documents)
                    
                    # Add conversation history as context for experts
                    conversation_context = []
                    if st.session_state.messages:
                        # Get last 5 conversation turns for context
                        recent_messages = st.session_state.messages[-10:]  # Last 5 exchanges
                        for msg in recent_messages:
                            conversation_context.append(f"{msg['role'].title()}: {msg['content']}")
                    
                    # Combine SOP context with conversation context
                    full_context = all_context + [f"Previous conversation:\n" + "\n".join(conversation_context)]
                    
                    # Consult experts with full context
                    consultation_result = multi_expert_system.consult_experts(prompt, full_context)
                    
                    # Display expert consultation results (using the existing display code)
                    experts_consulted = consultation_result['experts_consulted']
                    expert_responses = consultation_result['expert_responses']
                    consultation_summary = consultation_result['consultation_summary']
                    
                    # Header with experts consulted
                    if len(experts_consulted) == 1:
                        expert_name = experts_consulted[0]
                        expert_info = multi_expert_system.experts[expert_name]
                        st.markdown(f"#### 🎯 {expert_info.title} Analysis")
                    else:
                        st.markdown(f"#### 🏭 Multi-Expert Consultation ({len(experts_consulted)} experts)")
                        st.info(f"**Experts consulted:** {', '.join([multi_expert_system.experts[name].name for name in experts_consulted])}")
                    
                    # Display each expert's response (simplified version)
                    for expert_name, expert_response in expert_responses.items():
                        expert_info = multi_expert_system.experts[expert_name]
                        
                        if len(expert_responses) > 1:
                            st.markdown(f"### 👤 {expert_response['expert_title']}")
                        
                        # Main response
                        st.markdown(expert_response['main_response'], unsafe_allow_html=True)
                        
                        # Show recommendations in a compact format
                        if expert_response.get('recommendations'):
                            with st.expander(f"📋 {expert_info.name} Recommendations", expanded=False):
                                recs = expert_response['recommendations']
                                for timeframe, rec_list in recs.items():
                                    if rec_list:
                                        st.markdown(f"**{timeframe.replace('_', ' ').title()}:**")
                                        for rec in rec_list[:3]:  # Show top 3
                                            st.markdown(f"• {rec}")
                        
                        if len(expert_responses) > 1:
                            st.markdown("---")
                    
                    # Prepare response for chat history
                    if len(expert_responses) == 1:
                        response = list(expert_responses.values())[0]['main_response']
                    else:
                        expert_names = [multi_expert_system.experts[name].name for name in experts_consulted]
                        response = f"**Multi-Expert Consultation:** {', '.join(expert_names)}\n\n"
                        for expert_name, expert_resp in expert_responses.items():
                            expert_title = expert_resp['expert_title']
                            response += f"**{expert_title}:** {expert_resp['main_response'][:200]}...\n\n"
            
            else:
                # Standard knowledge search (no @mentions)
                with st.spinner("Searching knowledge base..."):
                    # Get response from SOP knowledge base
                    response, sop_sources = rag_handler.query(prompt)
                    
                    st.markdown(response, unsafe_allow_html=True)
                    
                    # Show SOP sources in a clean, collapsed format
                    if sop_sources:
                        with st.expander(f"📎 Reference Documents ({len(sop_sources)})", expanded=False):
                            for i, source in enumerate(sop_sources[:10]):  # Show max 10
                                if isinstance(source, dict) and 'gdrive_link' in source:
                                    # Clean filename display
                                    filename = source["filename"].replace(".doc", "").replace(".docx", "")
                                    st.markdown(f"{i+1}. [{filename}]({source['gdrive_link']})")
                                elif isinstance(source, dict):
                                    filename = source["filename"].replace(".doc", "").replace(".docx", "")
                                    st.markdown(f"{i+1}. {filename}")
                                else:
                                    filename = str(source).replace(".doc", "").replace(".docx", "")
                                    st.markdown(f"{i+1}. {filename}")
                            
                            if len(sop_sources) > 10:
                                st.caption(f"... and {len(sop_sources) - 10} more documents")
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    if not vector_db.has_documents():
        st.warning("⚠️ No documents found in the vector database. Click 'Check for Updates' to process your SOP documents.")
    

if __name__ == "__main__":
    main()