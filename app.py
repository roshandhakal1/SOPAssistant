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
from security_middleware import SecurityMiddleware, secure_session, validate_input

st.set_page_config(page_title="SOP Assistant", page_icon="📋", layout="wide")

# Force deployment update - v2025.01.02-GDRIVE-FIX
# DEPLOYMENT VERSION: Google Drive links + Advanced Market Analyst

# Require authentication before accessing the app
auth_manager = require_auth()

# SECURITY: Ensure session is valid and belongs to current user
if not auth_manager.is_session_valid():
    st.error("Session expired. Please log in again.")
    auth_manager.logout()
    st.rerun()

# Check if user settings should be shown
if hasattr(st.session_state, 'show_user_settings') and st.session_state.show_user_settings:
    from user_settings_interface import UserSettingsInterface
    
    st.markdown("# ⚙️ My Settings")
    
    if st.button("🔙 Back to Main App", type="secondary"):
        st.session_state.show_user_settings = False
        st.rerun()
    
    st.markdown("---")
    
    # Initialize user settings interface and render
    user_settings = UserSettingsInterface()
    user_settings.render_user_settings_page()
    st.stop()  # Stop here, don't render the main app

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
    """Simplified chat interface using sidebar mode selection"""
    
    # Get the selected mode from sidebar
    selected_mode = st.session_state.get('selected_mode', 'general')
    selected_experts = st.session_state.get('selected_experts', [])
    
    # Map mode to expert mention
    mode_to_expert = {
        'general': '',
        'quality': '@QualityExpert',
        'manufacturing': '@ManufacturingExpert',
        'accounting': '@AccountingExpert',
        'safety': '@SafetyExpert',
        'maintenance': '@MaintenanceExpert',
        'product_development': '@ProductDevelopmentExpert',
        'process_engineering': '@ProcessEngineeringExpert',
        'market_analysis': '@MarketAnalysisExpert',
        'advanced_market_analyst': '@AdvancedMarketAnalyst'
    }
    
    # Show current mode above chat input
    if selected_mode == 'multi' and selected_experts:
        # Multi-expert mode indicator
        expert_names = []
        for expert in selected_experts:
            if expert == 'quality':
                expert_names.append('🔬 Quality')
            elif expert == 'manufacturing':
                expert_names.append('🏭 Manufacturing')
            elif expert == 'accounting':
                expert_names.append('💰 Accounting')
            elif expert == 'safety':
                expert_names.append('🦺 Safety')
            elif expert == 'maintenance':
                expert_names.append('🔧 Maintenance')
            elif expert == 'product_development':
                expert_names.append('🧪 Formulation')
            elif expert == 'process_engineering':
                expert_names.append('⚙️ Process')
            elif expert == 'market_analysis':
                expert_names.append('📊 Market')
            elif expert == 'advanced_market_analyst':
                expert_names.append('🎯 Advanced Market')
        
        experts_text = ', '.join(expert_names)
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1rem;">
            <span style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; 
                         font-size: 0.9rem; color: #92400e; padding: 6px 16px; 
                         background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 20%); border-radius: 20px;">
                🎯 Multi-Expert Mode: {experts_text}
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Single mode indicator
        mode_names = {
            'general': '📚 General Search Mode',
            'quality': '🔬 Quality Expert Mode',
            'manufacturing': '🏭 Manufacturing Expert Mode',
            'accounting': '💰 Accounting Expert Mode',
            'safety': '🦺 Safety Expert Mode',
            'maintenance': '🔧 Maintenance Expert Mode',
            'product_development': '🧪 Formulation Scientist Mode',
            'process_engineering': '⚙️ Process Engineer Mode',
            'market_analysis': '📊 Market Analyst Mode'
        }
        
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1rem;">
            <span style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; 
                         font-size: 0.9rem; color: #86868b; padding: 6px 16px; 
                         background: rgba(0,0,0,0.05); border-radius: 20px;">
                {mode_names.get(selected_mode, '📚 General Search Mode')}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat input
    user_question = st.chat_input(
        "Ask your question...",
        key="main_chat_input"
    )
    
    # Process the input with selected mode
    if user_question:
        if selected_mode == 'multi' and selected_experts:
            # Multi-expert mode: add multiple @mentions
            expert_mentions = []
            for expert in selected_experts:
                if expert in mode_to_expert:
                    expert_mentions.append(mode_to_expert[expert])
            
            if expert_mentions:
                return f"{' '.join(expert_mentions)} {user_question}"
            else:
                return user_question
        else:
            # Single expert mode
            expert_prefix = mode_to_expert.get(selected_mode, '')
            if expert_prefix:
                return f"{expert_prefix} {user_question}"
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
    """Get file hash based on modification time and size for better stability"""
    try:
        stat = os.stat(file_path)
        # Use modification time and file size instead of content hash for stability
        hash_content = f"{stat.st_mtime}_{stat.st_size}".encode()
        return hashlib.md5(hash_content).hexdigest()
    except Exception:
        # Fallback to content hash if stat fails
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
        
        # Auto-processing check for new files (disabled by default to prevent constant reprocessing)
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
        # Expert Mode Selection - ALWAYS VISIBLE
        st.markdown("### 🎯 Assistant Mode")
        
        # Initialize selected mode if not exists
        if 'selected_mode' not in st.session_state:
            st.session_state.selected_mode = 'general'
        
        # Get available experts
        available_experts = multi_expert_system.get_available_experts()
        
        # Create mode options with better visual hierarchy
        st.markdown("""
        <style>
        .stRadio > label {
            font-size: 0.9rem !important;
            color: #86868b !important;
        }
        .stRadio > div {
            gap: 0.5rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Mode selection with clear visual feedback
        mode_col1, mode_col2 = st.columns([2, 2])
        
        with mode_col1:
            st.markdown("**Select Assistant Type:**")
        
        with mode_col2:
            # Add CSS to prevent text wrapping in toggle
            st.markdown("""
            <style>
            .stToggle label {
                white-space: nowrap !important;
                overflow: visible !important;
                text-overflow: clip !important;
                min-width: max-content !important;
            }
            .stToggle > div {
                min-width: max-content !important;
                width: auto !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            multi_mode = st.toggle("Multi", help="Multi-Expert Mode: Get insights from multiple experts at once")
        
        # Create cleaner mode options
        mode_options = {
            'general': {
                'name': '📚 General Search', 
                'short': 'General',
                'desc': 'Search across all SOPs and documentation'
            },
            'quality': {
                'name': '🔬 Quality Expert', 
                'short': 'Quality',
                'desc': 'FDA compliance, testing protocols, validation'
            },
            'manufacturing': {
                'name': '🏭 Manufacturing Expert', 
                'short': 'Manufacturing',
                'desc': 'Production systems, equipment, efficiency'
            },
            'accounting': {
                'name': '💰 Accounting Expert', 
                'short': 'Accounting',
                'desc': 'Cost analysis, financial controls, budgeting'
            },
            'safety': {
                'name': '🦺 Safety Expert', 
                'short': 'Safety',
                'desc': 'EHS compliance, OSHA, risk assessment'
            },
            'maintenance': {
                'name': '🔧 Maintenance Expert', 
                'short': 'Maintenance',
                'desc': 'Equipment reliability, preventive maintenance'
            },
            'product_development': {
                'name': '🧪 Formulation Scientist', 
                'short': 'Formulation',
                'desc': 'Nutritional biochemistry, supplement design, regulatory compliance'
            },
            'process_engineering': {
                'name': '⚙️ Process Engineer', 
                'short': 'Process',
                'desc': 'Industrial machinery, equipment diagnostics, process optimization'
            },
            'market_analysis': {
                'name': '📊 Market Analyst', 
                'short': 'Market',
                'desc': 'Competitive intelligence, market research, product analysis'
            }
        }
        
        if multi_mode:
            # Multi-select for multiple experts
            st.markdown("**Select multiple experts:**")
            
            # Expert options (excluding general for multi-mode)
            expert_options = {k: v for k, v in mode_options.items() if k != 'general'}
            
            selected_experts = st.multiselect(
                "",
                options=list(expert_options.keys()),
                format_func=lambda x: expert_options[x]['name'],
                default=[],
                key='multi_expert_selector',
                label_visibility="collapsed"
            )
            
            # Update session state for multi-mode
            st.session_state.selected_mode = 'multi'
            st.session_state.selected_experts = selected_experts
            
            # Show active experts
            if selected_experts:
                expert_names = [expert_options[exp]['short'] for exp in selected_experts]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 20%); 
                            padding: 12px; border-radius: 8px; margin-top: 8px;
                            border-left: 4px solid #f59e0b; width: 100%; box-sizing: border-box;">
                    <div style="font-weight: 600; color: #92400e; margin-bottom: 4px; 
                               white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                               min-width: 0; word-break: keep-all;">
                        Multi-Expert Mode: {', '.join(expert_names)}
                    </div>
                    <div style="font-size: 0.85rem; color: #78350f; 
                               white-space: normal; word-wrap: break-word;">
                        Get insights from multiple expert perspectives
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Select experts to get multiple perspectives on your questions")
        
        else:
            # Single select radio buttons
            selected_mode = st.radio(
                "",
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options[x]['name'],
                key='mode_selector',
                index=list(mode_options.keys()).index(st.session_state.selected_mode) if st.session_state.selected_mode in mode_options else 0,
                label_visibility="collapsed"
            )
            
            # Update session state
            st.session_state.selected_mode = selected_mode
            st.session_state.selected_experts = []  # Clear multi-select when in single mode
            
            # Show active mode with better styling
            if selected_mode in mode_options:
                mode_info = mode_options[selected_mode]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                            padding: 12px; border-radius: 8px; margin-top: 8px;
                            border-left: 4px solid #0284c7;">
                    <div style="font-weight: 600; color: #0c4a6e; margin-bottom: 4px;">
                        Currently Active: {mode_info['short']}
                    </div>
                    <div style="font-size: 0.85rem; color: #475569;">
                        {mode_info['desc']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Knowledge Base Status (simplified)
        try:
            collection_info = vector_db.get_collection_info()
            unique_docs = collection_info.get('unique_documents', 0)
            
            if unique_docs > 0:
                st.markdown(f"📄 **{unique_docs:,} SOPs** available")
            else:
                st.markdown("📄 **No documents** - Admin can sync in Admin Portal")
        except:
            st.markdown("📄 **Knowledge base** connection issue")
        
        st.divider()
        
        # Chat History Viewer
        with st.expander("📚 Chat History", expanded=False):
            username = st.session_state.get('username', 'unknown')
            recent_chats = chat_history_manager.get_recent_chats(username, limit=10)
            
            if recent_chats:
                st.markdown("**Recent Conversations:**")
                for i, chat in enumerate(recent_chats):
                    chat_title = chat.get('title', 'Untitled Chat')
                    chat_date = datetime.fromisoformat(chat.get('timestamp', '')).strftime('%m/%d %H:%M')
                    message_count = chat.get('message_count', 0)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        if st.button(f"💬 {chat_title}", key=f"load_chat_{i}", help=f"Load chat from {chat_date}"):
                            # Load the selected chat
                            st.session_state.messages = chat['messages'].copy()
                            st.rerun()
                    with col2:
                        st.caption(f"{message_count} msgs")
                    with col3:
                        if st.button("🗑️", key=f"delete_chat_{i}", help="Delete chat"):
                            chat_history_manager.delete_chat(username, chat['id'])
                            st.rerun()
                
                st.divider()
                if st.button("🗑️ Clear All History", type="secondary"):
                    chat_history_manager.clear_all_chats(username)
                    st.success("Chat history cleared!")
                    st.rerun()
            else:
                st.info("No chat history yet. Your conversations will be automatically saved here.")
        
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
        
        # User Settings Access (for all users)
        st.divider()
        
        # Check if user needs to change password
        username = st.session_state.get('username', '')
        user_data = {}
        try:
            from user_manager import UserManager
            user_manager = UserManager()
            user_data = user_manager.users.get(username, {})
        except:
            pass
        
        if user_data.get('must_change_password', False):
            st.warning("⚠️ Password change required")
        
        if st.button("⚙️ My Settings", use_container_width=True):
            st.session_state.show_user_settings = True
            st.rerun()
        
        # Admin Portal Access (only for admin users)
        if hasattr(st.session_state, 'user_role') and st.session_state.user_role == 'admin':
            st.divider()
            
            if st.button("🔧 Admin Portal", type="primary", use_container_width=True):
                st.session_state.show_admin_portal = True
                st.rerun()
            
            st.caption("🔐 Admin access available")
        
    
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Clean welcome
    if not st.session_state.messages:
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700;800&display=swap');
        
        .thinking-dots {
            display: inline-block;
        }
        
        .thinking-dots span {
            display: inline-block;
            opacity: 0.3;
            animation: thinking-pulse 1.4s ease-in-out infinite;
        }
        
        .thinking-dots span:nth-child(1) { animation-delay: 0s; }
        .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
        .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes thinking-pulse {
            0%, 80%, 100% { opacity: 0.3; }
            40% { opacity: 1; }
        }
        
        .main-title {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 4rem;
            font-weight: 800;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.05em;
            color: #1d1d1f !important;
            line-height: 0.9;
        }
        
        .main-subtitle {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1.3rem;
            font-weight: 500;
            margin: 0.5rem 0 2rem 0;
            color: #86868b !important;
        }
        </style>
        
        <div style="text-align: center; padding: 60px 0 40px 0;">
            <h1 style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 4rem; font-weight: 800; margin: 0 0 0.5rem 0; letter-spacing: -0.05em; color: #424242; line-height: 0.9;">SOP Assistant</h1>
            <p style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 1.3rem; font-weight: 500; margin: 0.5rem 0 2rem 0; color: #86868b;">Your intelligent knowledge companion</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Simple feature grid
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2rem; margin-bottom: 12px;">📚</div>
                <h4 style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0 0 8px 0; font-size: 1.1rem; font-weight: 600; color: #424242;">Smart Search</h4>
                <p style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; font-size: 0.9rem; color: #86868b;">Ask questions naturally</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2rem; margin-bottom: 12px;">👤</div>
                <h4 style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0 0 8px 0; font-size: 1.1rem; font-weight: 600; color: #424242;">Expert Consultation</h4>
                <p style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; font-size: 0.9rem; color: #86868b;">Specialized guidance</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Dynamic SOP count
        try:
            collection_info = vector_db.get_collection_info()
            unique_docs = collection_info.get('unique_documents', 0)
            
            # The unique_docs count should now be accurate (counting unique filenames)
            total_sops = unique_docs
            st.markdown(f"""
            <div style="text-align: center; margin: 20px auto; max-width: 300px;">
                <div style="padding: 12px; background: #f8f9fa; border-radius: 8px;">
                    <span style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 0.85rem; color: #495057;">📊 <strong>{total_sops:,} SOPs</strong> available for search</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("""
            <div style="text-align: center; margin: 20px auto; max-width: 300px;">
                <div style="padding: 12px; background: #f8f9fa; border-radius: 8px;">
                    <span style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 0.85rem; color: #495057;">📊 <strong>SOP Database</strong> ready for search</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
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
    
    # Fixed position chat interface at bottom
    st.markdown("""
    <div style="border-top: 1px solid #e0e0e0; padding-top: 1rem; margin-top: 2rem; background: rgba(248, 249, 250, 0.5); margin-left: -1rem; margin-right: -1rem; padding-left: 1rem; padding-right: 1rem; padding-bottom: 1rem;">
    </div>
    """, unsafe_allow_html=True)
    
    # Document attachment feature
    with st.expander("📎 Attach Document (Optional)", expanded=False):
        st.markdown("Upload a document to use as additional context for this conversation only.")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'docx', 'doc', 'txt'],
            help="Upload a document to provide additional context for your questions",
            key="chat_document_uploader"
        )
        
        # Initialize session state for attached documents
        if 'attached_documents' not in st.session_state:
            st.session_state.attached_documents = {}
        
        # Process uploaded document
        if uploaded_file is not None:
            try:
                # Validate file before processing
                valid, error_msg = SecurityMiddleware.validate_file_upload(uploaded_file)
                if not valid:
                    st.error(f"File validation failed: {error_msg}")
                    SecurityMiddleware.log_security_event("invalid_file_upload", {
                        "filename": uploaded_file.name,
                        "reason": error_msg
                    })
                    return
                
                # Sanitize filename
                safe_filename = SecurityMiddleware.sanitize_filename(uploaded_file.name)
                
                # Import document processor
                doc_processor = DocumentProcessor()
                
                # Process the uploaded file
                with st.spinner(f"Processing {safe_filename}..."):
                    # Save uploaded file temporarily
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Extract text from document
                        extracted_text = doc_processor.extract_text_from_file(tmp_file_path)
                        
                        if extracted_text and len(extracted_text.strip()) > 0:
                            # Store document content in session state
                            st.session_state.attached_documents[uploaded_file.name] = {
                                'content': extracted_text,
                                'filename': uploaded_file.name,
                                'size': len(extracted_text)
                            }
                            
                            st.success(f"✅ Document '{uploaded_file.name}' processed successfully!")
                            st.info(f"📄 **{len(extracted_text)} characters** extracted and ready to use as context")
                        else:
                            st.error("❌ Could not extract text from the document. Please try a different file.")
                    
                    finally:
                        # Clean up temporary file
                        if os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
                            
            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
        
        # Show currently attached documents
        if st.session_state.attached_documents:
            st.markdown("**📋 Currently Attached Documents:**")
            for filename, doc_info in st.session_state.attached_documents.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"• **{filename}** ({doc_info['size']:,} characters)")
                with col2:
                    if st.button("🗑️ Remove", key=f"remove_{filename}", help=f"Remove {filename}"):
                        del st.session_state.attached_documents[filename]
                        st.rerun()
    
    # Show attached documents indicator above chat input
    if st.session_state.get('attached_documents'):
        doc_count = len(st.session_state.attached_documents)
        doc_names = list(st.session_state.attached_documents.keys())
        if doc_count == 1:
            doc_text = f"📎 **{doc_names[0]}** attached"
        else:
            doc_text = f"📎 **{doc_count} documents** attached: {', '.join(doc_names[:2])}"
            if doc_count > 2:
                doc_text += f" and {doc_count - 2} more"
        
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 0.5rem;">
            <span style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; 
                         font-size: 0.8rem; color: #0066cc; padding: 4px 12px; 
                         background: rgba(0, 102, 204, 0.05); border-radius: 16px; border: 1px solid rgba(0, 102, 204, 0.1);">
                {doc_text}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    # Unified chat input with smart @mention detection
    prompt = handle_unified_chat_input(multi_expert_system)
    
    if prompt:
        # Validate and sanitize user input
        valid, sanitized_prompt, error_msg = validate_input(prompt, "text", max_length=2000)
        if not valid:
            st.error(f"Invalid input: {error_msg}")
            return
        
        # Additional security check for injection attempts
        valid, error_msg = SecurityMiddleware.validate_search_query(sanitized_prompt)
        if not valid:
            st.error(f"Security warning: {error_msg}")
            SecurityMiddleware.log_security_event("suspicious_query", {
                "query": SecurityMiddleware.hash_sensitive_data(prompt),
                "reason": error_msg
            })
            return
        
        prompt = sanitized_prompt
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Create assistant message container immediately
        with st.chat_message("assistant"):
            # Create a container for the entire response
            response_container = st.container()
            
            # Check if the prompt contains @mentions for expert consultation
            mentioned_experts = multi_expert_system.parse_mentions(prompt)
            
            if mentioned_experts:
                # Expert consultation with full conversation context
                with response_container:
                    # Show thinking animation in the same message bubble
                    thinking_placeholder = st.empty()
                    thinking_placeholder.markdown("""
                    <div style="padding: 10px 0;">
                        <div style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 1rem; color: #666;">
                            <span style="margin-right: 8px;">Consulting experts</span>
                            <span class="thinking-dots" style="font-size: 1rem;">
                                <span>•</span>
                                <span>•</span>
                                <span>•</span>
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                try:
                    # Get relevant SOPs and context
                    query_embedding = rag_handler.embeddings_manager.create_query_embedding(prompt)
                    sop_documents, sop_metadatas = vector_db.search(query_embedding, top_k=5)
                    
                    # Use SOP documents as context for expert consultation
                    all_context = []
                    if sop_documents:
                        all_context.extend(sop_documents)
                    
                    # Add attached documents as context
                    if st.session_state.get('attached_documents'):
                        for filename, doc_info in st.session_state.attached_documents.items():
                            # Add document content with clear identification
                            doc_context = f"**From attached document '{filename}':**\n{doc_info['content']}"
                            all_context.append(doc_context)
                    
                    # Add conversation history as context for experts
                    conversation_context = []
                    if st.session_state.messages:
                        # Get last 5 conversation turns for context
                        recent_messages = st.session_state.messages[-10:]  # Last 5 exchanges
                        for msg in recent_messages:
                            conversation_context.append(f"{msg['role'].title()}: {msg['content']}")
                    
                    # Combine SOP context with conversation context
                    full_context = all_context + [f"Previous conversation:\n" + "\n".join(conversation_context)]
                    
                    # Get user information for personalized responses
                    user_info = {
                        'name': st.session_state.get('user_name', ''),
                        'role': st.session_state.get('user_role', 'team member'),
                        'username': st.session_state.get('username', '')
                    }
                    
                    # Consult experts with full context and user info
                    consultation_result = multi_expert_system.consult_experts(prompt, full_context, user_info)
                    
                    # Extract results from consultation
                    experts_consulted = consultation_result['experts_consulted']
                    expert_responses = consultation_result['expert_responses']
                    consultation_summary = consultation_result['consultation_summary']
                    
                    # Clear thinking animation and display response in same container
                    thinking_placeholder.empty()
                    
                    # Check if this is a follow-up (recent expert responses in chat history)
                    recent_expert_response = False
                    if st.session_state.messages:
                        # Check last few messages for expert consultations
                        for msg in st.session_state.messages[-3:]:
                            if msg.get('role') == 'assistant' and ('Expert' in msg.get('content', '') or 'Consultation' in msg.get('content', '')):
                                recent_expert_response = True
                                break
                    
                    # Display the complete response in the placeholder
                    with thinking_placeholder.container():
                        # Header with experts consulted (only if not a follow-up)
                        if not recent_expert_response:
                            if len(experts_consulted) == 1:
                                expert_name = experts_consulted[0]
                                expert_info = multi_expert_system.experts[expert_name]
                                st.markdown(f"#### 🎯 {expert_info.title} Analysis")
                            else:
                                st.markdown(f"#### 🏭 Multi-Expert Consultation ({len(experts_consulted)} experts)")
                                st.info(f"**Experts consulted:** {', '.join([multi_expert_system.experts[name].name for name in experts_consulted])}")
                        
                        # Display each expert's response (clean professional format)
                        for expert_name, expert_response in expert_responses.items():
                            expert_info = multi_expert_system.experts[expert_name]
                            
                            # Only show expert titles for multi-expert AND not follow-up
                            if len(expert_responses) > 1 and not recent_expert_response:
                                st.markdown(f"### 👤 {expert_response['expert_title']}")
                            
                            # Main response - this now contains the full professional advice
                            st.markdown(expert_response['main_response'], unsafe_allow_html=True)
                            
                            # Follow-up questions if they exist and are contextual
                            follow_ups = expert_response.get('follow_up_questions', [])
                            if follow_ups and any(follow_up for follow_up in follow_ups if follow_up and 'aspect of' not in follow_up):
                                st.markdown("---")
                                st.markdown("**💡 Follow-up questions:**")
                                for question in follow_ups[:2]:
                                    if question and 'aspect of' not in question:
                                        st.markdown(f"• {question}")
                            
                            if len(expert_responses) > 1:
                                st.markdown("---")
                    
                    # Prepare response for chat history (preserve full format)
                    response_parts = []
                    
                    # Add header only if not a follow-up
                    if not recent_expert_response:
                        if len(experts_consulted) == 1:
                            expert_name = experts_consulted[0]
                            expert_info = multi_expert_system.experts[expert_name]
                            response_parts.append(f"#### 🎯 {expert_info.title} Analysis\n")
                        else:
                            expert_names = [multi_expert_system.experts[name].name for name in experts_consulted]
                            response_parts.append(f"#### 🏭 Multi-Expert Consultation ({len(experts_consulted)} experts)")
                            response_parts.append(f"**Experts consulted:** {', '.join(expert_names)}\n")
                    
                    # Add each expert's full response
                    for expert_name, expert_resp in expert_responses.items():
                        expert_title = expert_resp['expert_title']
                        
                        # Only show expert titles for multi-expert AND not follow-up
                        if len(expert_responses) > 1 and not recent_expert_response:
                            response_parts.append(f"### 👤 {expert_title}")
                        
                        response_parts.append(expert_resp['main_response'])
                        
                        if len(expert_responses) > 1:
                            response_parts.append("---")
                    
                    response = "\n\n".join(response_parts)
                    
                    # Save expert consultation response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Auto-save chat after assistant response
                    if len(st.session_state.messages) >= 2:  # At least one user + one assistant message
                        username = st.session_state.get('username', 'unknown')
                        chat_data = {
                            'messages': st.session_state.messages.copy(),
                            'mode': st.session_state.get('selected_mode', 'general')
                        }
                        chat_history_manager.save_chat(username, chat_data)
                    
                    return
                
                except Exception as e:
                    thinking_placeholder.empty()
                    st.error(f"Error during expert consultation: {str(e)}")
                    return
            
            else:
                # Standard knowledge search (no @mentions) WITH CONVERSATION CONTEXT
                with response_container:
                    # Show thinking animation in the same message bubble
                    thinking_placeholder = st.empty()
                    thinking_placeholder.markdown("""
                    <div style="padding: 10px 0;">
                        <div style="font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 1rem; color: #666;">
                            <span style="margin-right: 8px;">Searching knowledge base</span>
                            <span class="thinking-dots" style="font-size: 1rem;">
                                <span>•</span>
                                <span>•</span>
                                <span>•</span>
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                try:
                    # Build conversation context for follow-up questions
                    conversation_context = ""
                    if len(st.session_state.messages) > 1:  # If there's previous conversation
                        # Get last 4 exchanges for context (8 messages total)
                        recent_messages = st.session_state.messages[-8:]
                        context_parts = []
                        for msg in recent_messages:
                            context_parts.append(f"{msg['role'].title()}: {msg['content'][:200]}")
                        conversation_context = "\n".join(context_parts)
                    
                    # Add attached documents to context
                    attached_docs_context = ""
                    if st.session_state.get('attached_documents'):
                        attached_parts = []
                        for filename, doc_info in st.session_state.attached_documents.items():
                            attached_parts.append(f"**From attached document '{filename}':**\n{doc_info['content']}")
                        attached_docs_context = "\n\n".join(attached_parts)
                    
                    # Create enhanced prompt with conversation context and attached documents
                    prompt_parts = []
                    
                    if conversation_context:
                        prompt_parts.append(f"Previous conversation context:\n{conversation_context}")
                    
                    if attached_docs_context:
                        prompt_parts.append(f"Additional attached documents for context:\n{attached_docs_context}")
                    
                    prompt_parts.append(f"Current question: {prompt}")
                    
                    if conversation_context or attached_docs_context:
                        context_instruction = "Please answer the current question, taking into account"
                        if conversation_context and attached_docs_context:
                            context_instruction += " the conversation context and attached documents above."
                        elif conversation_context:
                            context_instruction += " the conversation context above. If this is a follow-up question, make sure to reference previous topics discussed."
                        elif attached_docs_context:
                            context_instruction += " the attached documents above for additional context."
                        prompt_parts.append(context_instruction)
                    
                    enhanced_prompt = "\n\n".join(prompt_parts) if len(prompt_parts) > 1 else prompt
                    
                    # Get response from SOP knowledge base with context
                    response, sop_sources = rag_handler.query(enhanced_prompt)
                    
                    # Clear thinking animation and display response in same container
                    thinking_placeholder.empty()
                    
                    # Display the complete response in the placeholder
                    with thinking_placeholder.container():
                        st.markdown(response, unsafe_allow_html=True)
                        
                        # Show SOP sources with prominent Google Drive links
                        if sop_sources:
                            # Check if any sources have Google Drive links
                            has_gdrive_links = any(isinstance(source, dict) and 'gdrive_link' in source for source in sop_sources)
                            
                            if has_gdrive_links:
                                expander_title = f"📎 Reference Documents ({len(sop_sources)}) - Click to open in Google Drive"
                            else:
                                expander_title = f"📎 Reference Documents ({len(sop_sources)})"
                            
                            with st.expander(expander_title, expanded=False):
                                for i, source in enumerate(sop_sources[:10]):  # Show max 10
                                    if isinstance(source, dict) and 'gdrive_link' in source:
                                        # Clean filename display with Google Drive link
                                        filename = source["filename"].replace(".doc", "").replace(".docx", "").replace(".pdf", "")
                                        # Use target="_blank" to open in new tab
                                        gdrive_url = source['gdrive_link']
                                        st.markdown(f"{i+1}. 📄 <a href='{gdrive_url}' target='_blank'>{filename}</a> 🔗", unsafe_allow_html=True)
                                    elif isinstance(source, dict) and 'filename' in source:
                                        filename = source["filename"].replace(".doc", "").replace(".docx", "").replace(".pdf", "")
                                        st.markdown(f"{i+1}. 📄 {filename}")
                                    else:
                                        filename = str(source).replace(".doc", "").replace(".docx", "").replace(".pdf", "")
                                        st.markdown(f"{i+1}. 📄 {filename}")
                                
                                if len(sop_sources) > 10:
                                    st.caption(f"... and {len(sop_sources) - 10} more documents")
                                
                                if has_gdrive_links:
                                    st.caption("💡 Click any linked document to open it in Google Drive")
                                else:
                                    st.caption("💡 To enable Google Drive links, sync documents in Admin Portal → Integration tab")
                
                except Exception as e:
                    thinking_placeholder.empty()
                    st.error(f"Error during search: {str(e)}")
                    return
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Auto-save chat after assistant response
        if len(st.session_state.messages) >= 2:  # At least one user + one assistant message
            username = st.session_state.get('username', 'unknown')
            chat_data = {
                'messages': st.session_state.messages.copy(),
                'mode': st.session_state.get('selected_mode', 'general')
            }
            chat_history_manager.save_chat(username, chat_data)
    
    if not vector_db.has_documents():
        st.warning("⚠️ No documents found in the vector database. Click 'Check for Updates' to process your SOP documents.")
    

if __name__ == "__main__":
    main()