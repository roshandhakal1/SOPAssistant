"""
Chat History Manager for SOP Assistant
Provides persistent chat history per user
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class ChatHistoryManager:
    """Manages persistent chat history for users."""
    
    def __init__(self, history_dir: str = "./chat_history"):
        self.history_dir = history_dir
        Path(history_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_user_file(self, username: str) -> str:
        """Get the file path for a user's chat history."""
        return os.path.join(self.history_dir, f"{username}_chats.json")
    
    def save_chat(self, username: str, chat_data: Dict) -> bool:
        """Save a chat session for a user."""
        try:
            user_file = self._get_user_file(username)
            
            # Load existing chats
            chats = self.load_user_chats(username)
            
            # Add new chat with timestamp
            chat_entry = {
                "id": f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "title": self._generate_chat_title(chat_data["messages"]),
                "mode": chat_data.get("mode", "standard"),
                "messages": chat_data["messages"],
                "message_count": len(chat_data["messages"])
            }
            
            chats.append(chat_entry)
            
            # Keep only last 50 chats to avoid file bloat
            chats = chats[-50:]
            
            # Save to file
            with open(user_file, 'w') as f:
                json.dump(chats, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving chat: {e}")
            return False
    
    def load_user_chats(self, username: str) -> List[Dict]:
        """Load all chats for a user."""
        try:
            user_file = self._get_user_file(username)
            if os.path.exists(user_file):
                with open(user_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading chats: {e}")
            return []
    
    def delete_chat(self, username: str, chat_id: str) -> bool:
        """Delete a specific chat."""
        try:
            chats = self.load_user_chats(username)
            chats = [chat for chat in chats if chat.get("id") != chat_id]
            
            user_file = self._get_user_file(username)
            with open(user_file, 'w') as f:
                json.dump(chats, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error deleting chat: {e}")
            return False
    
    def get_chat(self, username: str, chat_id: str) -> Optional[Dict]:
        """Get a specific chat by ID."""
        chats = self.load_user_chats(username)
        for chat in chats:
            if chat.get("id") == chat_id:
                return chat
        return None
    
    def _generate_chat_title(self, messages: List[Dict]) -> str:
        """Generate a title for the chat based on first user message."""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Take first 50 characters and clean up
                title = content[:50].strip()
                if len(content) > 50:
                    title += "..."
                return title if title else "New Chat"
        return "New Chat"
    
    def get_recent_chats(self, username: str, limit: int = 10) -> List[Dict]:
        """Get recent chats for a user."""
        chats = self.load_user_chats(username)
        # Sort by timestamp (newest first) and limit
        chats.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return chats[:limit]
    
    def clear_all_chats(self, username: str) -> bool:
        """Clear all chats for a user."""
        try:
            user_file = self._get_user_file(username)
            if os.path.exists(user_file):
                os.remove(user_file)
            return True
        except Exception as e:
            print(f"Error clearing chats: {e}")
            return False