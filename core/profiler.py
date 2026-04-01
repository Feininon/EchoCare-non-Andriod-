# core/profiler.py
import ollama
import json

class PsychologicalProfiler:
    """
    Analyzes free-text responses using LLM to determine psychological profile.
    """

    # Open-Ended Pivot Questions (from Paper Table I)
    QUESTIONS = [
        {
            "id": "axis_1",
            "axis": "Abstract vs Concrete",
            "question": "How would you explain the concept of 'Trust' to someone using only a physical object as a metaphor?",
            "analysis_guide": "Look for tangible, literal objects (Concrete) vs conceptual, ephemeral metaphors (Abstract)"
        },
        {
            "id": "axis_2",
            "axis": "Logic vs Harmony",
            "question": "If a close friend's business is failing because of their own poor management, do you tell them the harsh truth to save their money, or offer emotional support to save their confidence? Explain your reasoning.",
            "analysis_guide": "Look for efficiency/truth-focused reasoning (Logic) vs emotional safety/validation focus (Harmony)"
        },
        {
            "id": "axis_3",
            "axis": "Risk vs Security",
            "question": "Describe your ideal life five years from now. What does stability mean to you?",
            "analysis_guide": "Look for preference for predictability/safety (Security) vs excitement/variability (Risk)"
        },
        {
            "id": "axis_4",
            "axis": "Locus of Control",
            "question": "When you look back at your biggest mistake, what do you think caused it? How do you view your role in that outcome?",
            "analysis_guide": "Look for self-attribution/ownership (Internal) vs external circumstances/blame (External)"
        }
    ]

    @staticmethod
    def analyze_response(question_id, user_response):
        """
        Uses LLM to analyze free-text response and determine axis position.
        Returns: {"axis": "axis_1", "score": "Concrete", "confidence": 0.85}
        """
        
        question = next((q for q in PsychologicalProfiler.QUESTIONS if q["id"] == question_id), None)
        if not question:
            return None

        # Rule Book-guided analysis prompt
        analysis_prompt = f"""
        You are a psychological profiling analyzer. Analyze the user's response to determine their cognitive style.
        
        QUESTION: {question['question']}
        AXIS: {question['axis']}
        ANALYSIS GUIDE: {question['analysis_guide']}
        
        USER RESPONSE: "{user_response}"
        
        Based SOLELY on the language patterns, metaphors used, and reasoning style:
        - If the response uses tangible, literal, structured language → classify as first option
        - If the response uses conceptual, emotional, exploratory language → classify as second option
        
        Respond in JSON format ONLY:
        {{
            "axis": "{question_id}",
            "score": "Concrete" or "Abstract" or "Logic" or "Harmony" or "Security" or "Risk" or "Internal" or "External",
            "confidence": 0.0 to 1.0,
            "reasoning": "brief explanation of why"
        }}
        
        Be strict and objective. Do not be influenced by sentiment, only cognitive style.
        """

        try:
            response = ollama.chat(model="llama3.2", messages=[
                {"role": "system", "content": "You are a clinical psychological profiler. Analyze cognitive style objectively."},
                {"role": "user", "content": analysis_prompt}
            ])
            
            # Extract JSON from response
            result_text = response['message']['content'].strip()
            # Clean up markdown code blocks if present
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(result_text)
            
            return result
            
        except Exception as e:
            print(f"Analysis error: {e}")
            # Fallback to default
            return {"axis": question_id, "score": "Concrete", "confidence": 0.5, "reasoning": "Default due to analysis error"}

    @staticmethod
    def calculate_persona(answers):
        """
        Takes dict of {question_id: {"score": "...", "confidence": ...}}
        Returns complete persona profile.
        """
        profile = {
            "axis_1": answers.get("axis_1", {}).get("score", "Concrete"),
            "axis_2": answers.get("axis_2", {}).get("score", "Logic"),
            "axis_3": answers.get("axis_3", {}).get("score", "Security"),
            "axis_4": answers.get("axis_4", {}).get("score", "Internal"),
        }

        persona_name = PsychologicalProfiler._derive_persona_name(profile)
        style_instructions = PsychologicalProfiler._get_style_instructions(profile)

        return {
            "profile": profile,
            "persona_name": persona_name,
            "style_instructions": style_instructions,
            "completed_at": None
        }

    @staticmethod
    def _derive_persona_name(profile):
        # Map combinations to persona names
        p1 = profile["axis_1"]  # Concrete/Abstract
        p2 = profile["axis_2"]  # Logic/Harmony
        
        if p1 == "Concrete" and p2 == "Logic":
            return "Pragmatist Architect"
        elif p1 == "Concrete" and p2 == "Harmony":
            return "Supportive Guardian"
        elif p1 == "Abstract" and p2 == "Logic":
            return "Visionary Strategist"
        elif p1 == "Abstract" and p2 == "Harmony":
            return "Empathetic Advocate"
        else:
            return "Balanced Companion"

    @staticmethod
    def _get_style_instructions(profile):
        instructions = []
        
        # Axis 1: Abstract vs Concrete
        if profile["axis_1"] == "Concrete":
            instructions.append("Use structured, actionable steps and tangible evidence. Avoid vague metaphors.")
        else:
            instructions.append("Use conceptual frameworks and exploratory dialogue. Metaphors are acceptable.")
            
        # Axis 2: Logic vs Harmony
        if profile["axis_2"] == "Logic":
            instructions.append("Prioritize objective analysis and solution-oriented logic. Be direct and efficient.")
        else:
            instructions.append("Prioritize validation, empathy, and emotional containment before problem-solving.")
            
        # Axis 3: Risk vs Security
        if profile["axis_3"] == "Security":
            instructions.append("Introduce changes gradually and emphasize safety protocols. Be cautious and detailed.")
        else:
            instructions.append("You can propose more radical behavioral experiments but monitor for instability.")
            
        # Axis 4: Locus of Control
        if profile["axis_4"] == "Internal":
            instructions.append("Focus on agency, empowerment, and self-efficacy. Acknowledge their ownership.")
        else:
            instructions.append("Focus on coping mechanisms for external stressors. Validate environmental factors.")
            
        return " ".join(instructions)

    @staticmethod
    def get_questions():
        return PsychologicalProfiler.QUESTIONS