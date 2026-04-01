# models/schemas.py
from datetime import datetime

class UserProfileSchema:
    """
    Schema for User Profile Store (MongoDB).
    Includes the 4 Axes from Echo Care Paper.
    """
    @staticmethod
    def create_new(user_id, username, profile_data):
        return {
            "_id": user_id,
            "username": username,
            "password_hash": "", # Handled by auth
            "profile": {
                "axis_1": profile_data.get("axis_1", "Concrete"), # Abstract vs Concrete
                "axis_2": profile_data.get("axis_2", "Logic"),    # Logic vs Harmony
                "axis_3": profile_data.get("axis_3", "Security"), # Risk vs Security
                "axis_4": profile_data.get("axis_4", "Internal"), # Locus of Control
                "persona_name": profile_data.get("persona_name", "Balanced Companion"),
                "style_instructions": profile_data.get("style_instructions", "")
            },
            "profiling_completed": False,
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }

    @staticmethod
    def update_profile(existing_doc, new_profile_data):
        """Updates profile while preserving history."""
        existing_doc["profile"].update(new_profile_data)
        existing_doc["last_updated"] = datetime.now()
        return existing_doc

class ConversationSchema:
    """
    Schema for Conversation Logs (MongoDB).
    Includes metadata for Feedback Loop.
    """
    @staticmethod
    def create_entry(user_id, user_msg, bot_msg, metadata=None):
        return {
            "user_id": user_id,
            "user_message": user_msg,
            "bot_response": bot_msg,
            "timestamp": datetime.now(),
            "metadata": metadata or {
                "crisis_flag": False,
                "tone_shift": False,
                "persona_used": "default"
            }
        }