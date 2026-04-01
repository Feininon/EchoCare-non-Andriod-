# core/tone_analyzer.py

class ToneAnalyzer:
    """
    Detects shifts in user tone to override static profiling (Paper Section III.D).
    """

    DISTRESS_INDICATORS = [
        "i'm not okay", "this is too much", "overwhelmed", "can't handle", 
        "breaking down", "screaming", "crying", "panic", "shaking"
    ]

    @staticmethod
    def detect_distress_shift(message):
        """
        Returns True if current message indicates high distress vs normal profile.
        """
        message_lower = message.lower()
        score = 0
        
        # Check for direct distress cues
        for indicator in ToneAnalyzer.DISTRESS_INDICATORS:
            if indicator in message_lower:
                score += 1
        
        # Check for length collapse (sudden short messages can indicate shock)
        # This logic would ideally compare against history, but simple check for now
        if len(message) < 10 and "?" not in message and "." not in message:
            score += 1
            
        return score >= 2  # Threshold for shift

    @staticmethod
    def get_adaptation_instruction(is_distressed):
        """
        Returns prompt instruction to adjust tone based on current state.
        """
        if is_distressed:
            return "URGENT TONE SHIFT: User is currently distressed. Prioritize validation, calming language, and safety over logical problem solving. Be gentle."
        else:
            return "Maintain consistent persona alignment."