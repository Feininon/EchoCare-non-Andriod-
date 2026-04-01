# core/profiler.py
import ollama
import json
import re

class PsychologicalProfiler:
    """
    Invisible profiling: Analyzes free-text responses using LLM.
    User sees only natural conversation prompts.
    """

    # Pivot Questions - NO axis labels shown to user
    QUESTIONS = [
        {
            "id": "axis_1",
            "question": "How would you explain the concept of 'Trust' to someone using only a physical object as a metaphor?"
        },
        {
            "id": "axis_2", 
            "question": "If a close friend's business is failing because of their own poor management, do you tell them the harsh truth to save their money, or offer emotional support to save their confidence? Explain your reasoning."
        },
        {
            "id": "axis_3",
            "question": "Describe your ideal life five years from now. What does stability mean to you?"
        },
        {
            "id": "axis_4",
            "question": "When you look back at your biggest mistake, what do you think caused it? How do you view your role in that outcome?"
        }
    ]

    # Internal mapping for analysis (never shown to user)
    _AXIS_MAP = {
        "axis_1": {"options": ["Concrete", "Abstract"], "guide": "tangible/literal vs conceptual/ephemeral language"},
        "axis_2": {"options": ["Logic", "Harmony"], "guide": "efficiency/truth focus vs emotional safety focus"},
        "axis_3": {"options": ["Security", "Risk"], "guide": "preference for predictability vs excitement/variability"},
        "axis_4": {"options": ["Internal", "External"], "guide": "self-attribution vs external circumstances"}
    }

    @staticmethod
    def analyze_response(question_id, user_response):
        """
        Backend-only LLM analysis. Returns structured profile data.
        """
        axis_info = PsychologicalProfiler._AXIS_MAP.get(question_id)
        if not axis_info:
            return None

        # Strict, internal analysis prompt (user never sees this)
        analysis_prompt = f"""
        You are a clinical psychological profiler. Analyze the user's response to determine their cognitive style.
        
        Question: "{PsychologicalProfiler._get_question_text(question_id)}"
        Analysis Focus: {axis_info['guide']}
        
        User Response: "{user_response}"
        
        Instructions:
        - Analyze ONLY language patterns, metaphors, and reasoning style
        - Ignore sentiment, politeness, or social desirability
        - Be strict and objective
        
        Respond in JSON format ONLY:
        {{
            "axis": "{question_id}",
            "score": "{axis_info['options'][0]}" or "{axis_info['options'][1]}",
            "confidence": 0.0 to 1.0,
            "reasoning": "one sentence explanation"
        }}
        """

        try:
            response = ollama.chat(model="llama3.2", messages=[
                {"role": "system", "content": "You are a clinical psychological profiler. Analyze cognitive style objectively."},
                {"role": "user", "content": analysis_prompt}
            ])
            
            result_text = response['message']['content'].strip()
            result_text = re.sub(r'```json|```', '', result_text).strip()
            result = json.loads(result_text)
            
            return result
            
        except Exception as e:
            print(f"Profiling analysis error: {e}")
            # Fallback to first option with low confidence
            return {
                "axis": question_id, 
                "score": axis_info["options"][0], 
                "confidence": 0.5, 
                "reasoning": "Default due to analysis uncertainty"
            }

    @staticmethod
    def _get_question_text(qid):
        q = next((q for q in PsychologicalProfiler.QUESTIONS if q["id"] == qid), None)
        return q["question"] if q else ""

    @staticmethod
    def calculate_persona(answers):
        """
        Takes dict of {question_id: {"score": "...", "confidence": ...}}
        Returns complete persona profile (backend only).
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
        
        if profile["axis_1"] == "Concrete":
            instructions.append("Use structured, actionable steps and tangible evidence.")
        else:
            instructions.append("Use conceptual frameworks and exploratory dialogue.")
            
        if profile["axis_2"] == "Logic":
            instructions.append("Prioritize objective analysis and solution-oriented logic.")
        else:
            instructions.append("Prioritize validation, empathy, and emotional containment.")
            
        if profile["axis_3"] == "Security":
            instructions.append("Introduce changes gradually and emphasize safety.")
        else:
            instructions.append("You can propose more radical behavioral experiments.")
            
        if profile["axis_4"] == "Internal":
            instructions.append("Focus on agency, empowerment, and self-efficacy.")
        else:
            instructions.append("Focus on coping mechanisms for external stressors.")
            
        return " ".join(instructions)

    @staticmethod
    def get_questions():
        return PsychologicalProfiler.QUESTIONS