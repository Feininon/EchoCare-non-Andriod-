# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pymongo
import uuid
from datetime import datetime
import ollama
import os

# --- Import Core Modules (Batch 1) ---
from core.profiler import PsychologicalProfiler
from core.rulebook import RuleBook
from core.tone_analyzer import ToneAnalyzer

# --- Import Utils & Data (Batch 2) ---
from utils.faiss_manager import FAISSManager
from models.schemas import UserProfileSchema, ConversationSchema
from data.crisis_resources import get_crisis_response

# ---------------------------
# Initialization
# ---------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey_change_in_production"
bcrypt = Bcrypt(app)

# Database Connection
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["mental_health_chatbot"]
users_collection = db["users"]
chat_collection = db["documents"] # Conversation Logs

# Initialize Managers
faiss_manager = FAISSManager()

# ---------------------------
# Flask-Login Configuration
# ---------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({"_id": user_id})
    if user:
        return User(user["_id"], user["username"])
    return None

# ---------------------------
# Helper Functions
# ---------------------------
def get_user_profile():
    """Fetch current user's psychological profile from DB."""
    user_doc = users_collection.find_one({"_id": current_user.id})
    if user_doc and "profile" in user_doc:
        return user_doc["profile"]
    return None

def save_chat_to_db(user_id, user_msg, bot_msg, metadata):
    """Save conversation to MongoDB."""
    entry = ConversationSchema.create_entry(user_id, user_msg, bot_msg, metadata)
    chat_collection.insert_one(entry)

# ---------------------------
# Routes: Authentication
# ---------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if users_collection.find_one({"username": username}):
            flash("Username already exists.")
            return redirect(url_for("signup"))

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        user_id = str(uuid.uuid4())
        
        # Create User Profile Schema (Profiling Completed = False initially)
        profile_data = PsychologicalProfiler.calculate_persona({}) # Default temp profile
        user_doc = UserProfileSchema.create_new(user_id, username, profile_data)
        user_doc["password_hash"] = hashed_pw # Store securely
        
        users_collection.insert_one(user_doc)
        flash("Signup successful! Please log in.")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users_collection.find_one({"username": username})

        if user and bcrypt.check_password_hash(user["password_hash"], password):
            login_user(User(user["_id"], username))
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------------------
# Routes: Profiling Wizard
# ---------------------------
@app.route("/profiling", methods=["GET", "POST"])
@login_required
def profiling_wizard():
    user_doc = users_collection.find_one({"_id": current_user.id})
    if user_doc.get("profiling_completed"):
        return redirect(url_for("index"))

    if request.method == "POST":
        answers = {}
        for question in PsychologicalProfiler.get_questions():
            q_id = question["id"]
            user_response = request.form.get(q_id, "").strip()
            
            if user_response:
                # Silent backend analysis
                analysis = PsychologicalProfiler.analyze_response(q_id, user_response)
                answers[q_id] = analysis
        
        profile_result = PsychologicalProfiler.calculate_persona(answers)
        profile_result["completed_at"] = datetime.now()
        
        users_collection.update_one(
            {"_id": current_user.id},
            {"$set": {"profile": profile_result, "profiling_completed": True}}
        )
        flash("Thanks for sharing! Let's begin.")
        return redirect(url_for("index"))

    questions = PsychologicalProfiler.get_questions()
    return render_template("profiling_wizard.html", questions=questions)

# Optional: Real-time analysis endpoint (for progressive profiling)
@app.route("/analyze_response", methods=["POST"])
@login_required
def analyze_response():
    """API endpoint for real-time response analysis"""
    data = request.get_json()
    question_id = data.get("question_id")
    user_response = data.get("response")
    
    if not question_id or not user_response:
        return jsonify({"error": "Missing data"}), 400
    
    analysis = PsychologicalProfiler.analyze_response(question_id, user_response)
    return jsonify(analysis)

# ---------------------------
# Routes: Main Chat Interface
# ---------------------------
@app.route("/")
@login_required
def index():
    # Force Profiling if not done
    user_doc = users_collection.find_one({"_id": current_user.id})
    if not user_doc.get("profiling_completed"):
        return redirect(url_for("profiling_wizard"))
        
    return render_template("index.html", username=current_user.username)

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    """
    Core Intelligence Layer Orchestrator.
    Flow: Input -> Safety -> Tone -> Context -> LLM -> Output
    """
    data = request.get_json()
    user_input = data.get("message", "")

    if not user_input:
        return jsonify({"error": "No message"}), 400

    # 1. Load User Profile & FAISS Index
    profile = get_user_profile()
    faiss_index = faiss_manager.load_index(current_user.id)
    
    # 2. Tier 1: Safety Classifier (Rule Book)
    if RuleBook.check_safety_trigger(user_input):
        bot_response = get_crisis_response()
        metadata = {"crisis_flag": True, "tone_shift": False}
        save_chat_to_db(current_user.id, user_input, bot_response, metadata)
        # Do NOT store crisis messages in FAISS for context retrieval (safety)
        return jsonify({"bot_response": bot_response, "is_crisis": True})

    # 3. Dynamic Adaptation: Tone Analyzer
    is_distressed = ToneAnalyzer.detect_distress_shift(user_input)
    tone_instruction = ToneAnalyzer.get_adaptation_instruction(is_distressed)

    # 4. Context Assembly (FAISS)
    context = faiss_manager.retrieve_context(current_user.id, user_input, faiss_index, top_k=3)

    # 5. Construct Prompt (Rule Book Tier 2 & 3)
    system_prompt = RuleBook.get_system_prompt(profile["style_instructions"] if profile else "")
    
    # Add Tone Shift Instruction if needed
    if is_distressed:
        system_prompt += f"\n{tone_instruction}"

    # Build Message History for LLM
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    if context:
        messages.append({"role": "system", "content": f"Relevant Context from History:\n{context}"})
        
    messages.append({"role": "user", "content": user_input})

    # 6. LLM Inference Engine (Ollama)
    try:
        response = ollama.chat(model="llama3.2", messages=messages)
        bot_response = response['message']['content']
    except Exception as e:
        bot_response = "I'm having trouble connecting right now. Please try again."

    # 7. Save to Memory (DB + FAISS)
    metadata = {"crisis_flag": False, "tone_shift": is_distressed, "persona_used": profile["persona_name"]}
    save_chat_to_db(current_user.id, user_input, bot_response, metadata)
    
    # Store in Vector DB for future retrieval
    faiss_manager.add_message(current_user.id, user_input, "user", faiss_index)
    faiss_manager.add_message(current_user.id, bot_response, "bot", faiss_index)
    faiss_manager.save_index(current_user.id, faiss_index)

    return jsonify({"bot_response": bot_response, "is_crisis": False})

@app.route("/history")
@login_required
def chat_history():
    """Fetch chat history for UI."""
    user_id = current_user.id
    history = {}
    chats = chat_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(100)

    for chat in chats:
        date = chat["timestamp"].strftime("%Y-%m-%d")
        time = chat["timestamp"].strftime("%I:%M %p")
        if date not in history:
            history[date] = []
        history[date].append({
            "time": time,
            "user_message": chat["user_message"],
            "bot_response": chat["bot_response"]
        })

    return jsonify(history)

if __name__ == "__main__":
    app.run(debug=True, port=5000)