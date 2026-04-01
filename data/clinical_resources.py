# data/clinical_resources.py

"""
Vetted Clinical Resources for Context Assembly.
Matches Architecture: Data & Memory Layer (Clinical Resources DB)
"""

CBT_TECHNIQUES = {
    "reframing": "Cognitive Reframing: Identify the negative thought, challenge its evidence, and replace it with a balanced perspective.",
    "grounding": "5-4-3-2-1 Grounding: Acknowledge 5 things you see, 4 you can touch, 3 you hear, 2 you can smell, 1 you can taste.",
    "breathing": "Box Breathing: Inhale for 4 counts, hold for 4, exhale for 4, hold for 4. Repeat 4 times.",
    "behavioral_activation": "Behavioral Activation: Break down overwhelming tasks into tiny, manageable steps (e.g., just put on shoes)."
}

COPING_STRATEGIES = {
    "anxiety": [
        "Focus on what you can control right now.",
        "Write down your worries to externalize them.",
        "Practice progressive muscle relaxation."
    ],
    "depression": [
        "Acknowledge small wins today.",
        "Connect with one safe person.",
        "Maintain basic routine (sleep, food, hygiene)."
    ],
    "overwhelm": [
        "Stop and pause. You don't need to solve everything now.",
        "Prioritize one single task.",
        "Step away from screens for 10 minutes."
    ]
}

PSYCHOEDUCATION = {
    "panic_attack": "Panic attacks feel dangerous but are not harmful. They peak within 10 minutes and then subside. Focus on slowing your exhale.",
    "insomnia": "Sleep hygiene involves keeping a consistent schedule and avoiding screens 1 hour before bed.",
    "stress": "Stress is a physical response. Movement helps process stress hormones."
}

def get_resource(topic):
    """Helper to retrieve resources by topic."""
    topic = topic.lower()
    if topic in CBT_TECHNIQUES:
        return CBT_TECHNIQUES[topic]
    if topic in COPING_STRATEGIES:
        return COPING_STRATEGIES[topic]
    if topic in PSYCHOEDUCATION:
        return PSYCHOEDUCATION[topic]
    return None