# core/rulebook.py

class RuleBook:
    """
    Implements the 3-Tier Rule Book from Echo Care Paper.
    Tier 1: Safety (Hard Override)
    Tier 2: Ethics (Hard Constraint)
    Tier 3: Therapeutic Alignment (Soft Guidance)
    """

    # Tier 1: Crisis Keywords (Expanded from your original list)
    CRISIS_KEYWORDS = [
        "suicide", "hopeless", "self-harm", "end my life", "no reason to live", 
        "can't go on", "kill myself", "want to die", "hurt myself", "no way out",
        "ending it all", "goodbye forever"
    ]

    # Tier 2: Ethical Boundaries (System Prompt Injections)
    ETHICAL_CONSTRAINTS = """
    - DO NOT diagnose medical conditions.
    - DO NOT prescribe medication or suggest dosages.
    - DO NOT claim to be a doctor or licensed therapist.
    - DO NOT guarantee success rates or cures.
    - If asked about medication, refer to a physician.
    - You are a supportive AI companion, NOT a replacement for clinical care.
    """

    # Tier 1: Crisis Response Template
    CRISIS_RESPONSE = """
    💙 I'm really sorry you're feeling this way. You're not alone.
    📞 Please reach out to a trusted friend, family member, or professional immediately.
    🆘 Find a mental health helpline here: https://findahelpline.com/
    🚨 If you are in immediate danger, please call emergency services.
    """

    @staticmethod
    def check_safety_trigger(message):
        """
        Tier 1 Check: Returns True if crisis detected.
        """
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in RuleBook.CRISIS_KEYWORDS)

    @staticmethod
    def get_system_prompt(persona_instructions=None):
        """
        Constructs the full System Prompt combining Tier 2 & Tier 3.
        Tier 1 is handled separately in logic flow.
        """
        base_prompt = """
        You are EchoCare, a compassionate mental health support AI.
        Your goal is to provide emotional support, mindfulness tips, and mental well-being advice.
        You are a 'non-judgmental void' for catharsis, helping users organize their thoughts.
        You do NOT give life advice or make decisions for the user.
        """
        
        prompt = base_prompt + "\n" + RuleBook.ETHICAL_CONSTRAINTS + "\n"
        
        if persona_instructions:
            prompt += f"\nUSER PERSONA STYLE (Tier 3 Alignment): {persona_instructions}\n"
            prompt += "Adapt your tone to match this style while maintaining safety."
            
        prompt += "\n\nKeep responses concise (under 100 words) unless asked for more."
        
        return prompt

    @staticmethod
    def get_crisis_response():
        return RuleBook.CRISIS_RESPONSE