# data/crisis_resources.py

"""
Emergency Resources for Crisis Intervention.
Matches Architecture: Core Intelligence Layer (Safety Classifier)
"""

CRISIS_MESSAGE = """
💙 I'm really sorry you're feeling this way. You are not alone.
📞 Please reach out to a trusted friend, family member, or professional immediately.
🆘 Find a mental health helpline here: https://findahelpline.com/
🚨 If you are in immediate danger, please call emergency services (911/112/999).
"""

HELPLINES = {
    "US": "988 Suicide & Crisis Lifeline",
    "UK": "111 or Samaritans (116 123)",
    "IN": "Kirans Helpline (1800-599-0019)",
    "GLOBAL": "https://findahelpline.com/"
}

def get_crisis_response():
    return CRISIS_MESSAGE