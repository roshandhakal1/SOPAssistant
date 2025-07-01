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
from session_document_handler import SessionDocumentHandler
from auth import require_auth
from chat_history_manager import ChatHistoryManager
from cloud_storage import CloudStorageUI

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

def handle_unified_chat_input(multi_expert_system):
    """Unified chat input with inline @mention autocomplete"""
    
    # Simple chat input with placeholder that hints at @mention functionality
    placeholder = "Ask about your SOPs or @mention experts (e.g., @QualityExpert, @ManufacturingExpert)..."
    
    # Use regular chat input - streamlit's built-in is cleaner
    user_input = st.chat_input(placeholder)
    
    return user_input

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
                st.info("🔄 Knowledge base is empty. Checking for documents...")
                
                # Try auto-sync from Google Drive if configured
                if config.AUTO_SYNC_ON_STARTUP and config.GOOGLE_DRIVE_FOLDER_ID:
                    try:
                        from cloud_storage import GoogleDriveManager
                        gdrive = GoogleDriveManager()
                        
                        if gdrive.load_saved_credentials():
                            with st.spinner("🔄 Auto-syncing from Google Drive..."):
                                # Use preferred sync folder if set, otherwise use main folder
                                sync_folder_id = st.session_state.get('preferred_sync_folder', config.GOOGLE_DRIVE_FOLDER_ID)
                                downloaded_files = gdrive.sync_folder(sync_folder_id, config.SOP_FOLDER)
                                if downloaded_files:
                                    folder_name = "preferred subfolder" if sync_folder_id != config.GOOGLE_DRIVE_FOLDER_ID else "main folder"
                                    st.success(f"✅ Auto-synced {len(downloaded_files)} documents from Google Drive ({folder_name})!")
                    except Exception as e:
                        st.warning("⚠️ Auto-sync failed. Manual upload available in Document Management.")
                
                # Check for any documents (local or synced)
                updates, removed_files, new_index = check_for_updates(
                    config, doc_processor, embeddings_manager, vector_db
                )
                if updates:
                    st.info("Found documents. Processing...")
                    process_updates(updates, removed_files, new_index, 
                                  doc_processor, embeddings_manager, vector_db)
                else:
                    st.info("💡 No documents found. Use Document Management in sidebar to upload files.")
            
            st.session_state.initialized = True
    else:
        # Use cached components if available
        if 'components' in st.session_state:
            config, doc_processor, embeddings_manager, vector_db, session_doc_handler, chat_history_manager = st.session_state.components
        else:
            components = initialize_components()
            st.session_state.components = components
            config, doc_processor, embeddings_manager, vector_db, session_doc_handler, chat_history_manager = components
        
    
    # Get model-specific components based on user settings (after component initialization)
    rag_handler, multi_expert_system, standard_model, expert_model = get_model_components(config, vector_db)
    
    with st.sidebar:
        st.header("🏭 Manufacturing Knowledge Assistant")
        st.success("💬 **Smart Chat Mode** - Ask questions or @mention experts for specialized insights")
        
        # Always show available experts in a compact format
        with st.expander("🎯 Available Experts", expanded=False):
            available_experts = multi_expert_system.get_available_experts()
            
            st.markdown("**Type @ in chat to see expert suggestions:**")
            
            # Show experts in a more compact 2-column format
            expert_list = list(available_experts.items())
            for i in range(0, len(expert_list), 2):
                col1, col2 = st.columns(2)
                
                with col1:
                    if i < len(expert_list):
                        expert_name, expert_info = expert_list[i]
                        st.markdown(f"**@{expert_name}**")
                        st.caption(expert_info['title'][:30] + "...")
                
                with col2:
                    if i + 1 < len(expert_list):
                        expert_name, expert_info = expert_list[i + 1]
                        st.markdown(f"**@{expert_name}**")
                        st.caption(expert_info['title'][:30] + "...")
            
            st.info("💡 **Examples:**\n- What are the cleaning validation requirements?\n- @QualityExpert how do we validate this procedure?\n- @ManufacturingExpert @ProcessEngineeringExpert help optimize our mixing process")
        
        st.divider()
        
        # Document Management with Google Drive Integration
        with st.expander("📁 Document Management", expanded=False):
            st.caption(f"Knowledge Base: {config.SOP_FOLDER}")
            
            # Google Drive Integration
            st.subheader("☁️ Google Drive Sync")
            
            from cloud_storage import GoogleDriveManager
            gdrive = GoogleDriveManager()
            
            if gdrive.load_saved_credentials():
                st.success("✅ Connected to Google Drive")
                
                # Show configured folder info
                if config.GOOGLE_DRIVE_FOLDER_ID:
                    st.info(f"📂 **Main Folder**: Gemini Training (`{config.GOOGLE_DRIVE_FOLDER_ID}`)")
                    
                    # List subfolders and show document count
                    subfolders = gdrive.list_folders(config.GOOGLE_DRIVE_FOLDER_ID)
                    if subfolders:
                        # Add option to sync main folder directly
                        folder_options = {"📂 Main Folder (Gemini Training)": config.GOOGLE_DRIVE_FOLDER_ID}
                        for folder in subfolders:
                            # Get document count for each folder (with pagination)
                            doc_count = len(gdrive.list_documents(folder['id']))
                            folder_options[f"📁 {folder['name']} ({doc_count} docs)"] = folder['id']
                        
                        selected_sync_folder = st.selectbox(
                            "Select folder to sync documents from:",
                            options=list(folder_options.keys()),
                            key="sync_folder_selection"
                        )
                        
                        if selected_sync_folder:
                            folder_id = folder_options[selected_sync_folder]
                            
                            # Show total documents in selected folder
                            documents = gdrive.list_documents(folder_id)
                            if documents:
                                st.info(f"📄 **{len(documents)} documents** found in this folder")
                                
                                if st.button("🚀 Sync to Knowledge Base", type="primary", use_container_width=True):
                                    with st.spinner(f"Syncing {len(documents)} documents from Google Drive..."):
                                        # Clear documents folder first to avoid duplicates
                                        import shutil
                                        if Path(config.SOP_FOLDER).exists():
                                            shutil.rmtree(config.SOP_FOLDER)
                                        Path(config.SOP_FOLDER).mkdir(parents=True, exist_ok=True)
                                        
                                        # Sync files
                                        downloaded_files = gdrive.sync_folder(folder_id, config.SOP_FOLDER)
                                        
                                        if downloaded_files:
                                            # Process all files into knowledge base
                                            updates, removed_files, new_index = check_for_updates(
                                                config, doc_processor, embeddings_manager, vector_db
                                            )
                                            
                                            if updates:
                                                process_updates(updates, removed_files, new_index, 
                                                              doc_processor, embeddings_manager, vector_db)
                                            
                                            # Save this folder as the preferred sync folder
                                            st.session_state.preferred_sync_folder = folder_id
                                            
                                            st.success(f"✅ **{len(downloaded_files)} documents** synced and processed into knowledge base!")
                                            st.info("💡 Your knowledge base is now ready for questions!")
                                        else:
                                            st.error("❌ No documents were synced")
                            else:
                                st.warning("No supported documents found in this folder")
                    else:
                        st.warning("No subfolders found in the main folder")
            else:
                st.info("🔗 Connect Google Drive to sync documents automatically")
                if st.button("🔐 Connect Google Drive", use_container_width=True):
                    st.info("Go to Admin Portal to set up Google Drive integration")
            
            st.divider()
            
            # Document management for all users
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
    
    # Visual indicator for unified interface
    st.info("🏭 **Smart Assistant** | Ask questions or @mention experts for specialized insights | Available: @QualityExpert, @ManufacturingExpert, @ProcessEngineeringExpert, etc.")
    
    # Show document context indicator
    if st.session_state.uploaded_documents:
        doc_count = len(st.session_state.uploaded_documents)
        st.success(f"📎 {doc_count} reference document{'s' if doc_count != 1 else ''} loaded for this conversation")
    
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
                            for source in sop_sources:
                                if isinstance(source, dict) and 'gdrive_link' in source:
                                    # Source with Google Drive link
                                    st.markdown(f'<span class="sop-reference">{source["filename"]}</span> [📁 Open in Drive]({source["gdrive_link"]})', unsafe_allow_html=True)
                                elif isinstance(source, dict):
                                    # Source without link
                                    st.markdown(f'<span class="sop-reference">{source["filename"]}</span>', unsafe_allow_html=True)
                                else:
                                    # Legacy format (just filename string)
                                    st.markdown(f'<span class="sop-reference">{source}</span>', unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    if not vector_db.has_documents():
        st.warning("⚠️ No documents found in the vector database. Click 'Check for Updates' to process your SOP documents.")
    

if __name__ == "__main__":
    main()