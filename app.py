from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

# Setup Flask and OpenAI
app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Memory Functions ---
def load_memory(user_id):
    filepath = f"user_memory/{user_id}.txt"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return f.read()
    return ""

def save_memory(user_id, content):
    filepath = f"user_memory/{user_id}.txt"
    os.makedirs("user_memory", exist_ok=True)
    
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            existing = f.read()
        if content not in existing:
            with open(filepath, "a") as f:
                f.write("\n" + content)
    else:
        with open(filepath, "w") as f:
            f.write(content)

def extract_relevant_info(conversation):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract only the user's health goals, dietary preferences, restrictions, and supplement habits from this message. "
                    "Do not include the full conversation. Only save concise, useful facts you would remember as their personal coach."
                )
            },
            {"role": "user", "content": conversation}
        ]
    )
    return response.choices[0].message.content

# --- Routes ---
@app.route("/")
def home():
    return "🚀 FuelNaturally AI backend is live!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")
    user_id = data.get("user_id", "default_user")
    memory = load_memory(user_id)
    lower_input = user_input.lower()
    model = "gpt-4o"

    supplement_keywords = [
        "supplement", "creatine", "turkesterone", "protein powder", "magnesium", "zinc",
        "fish oil", "vitamin", "ashwagandha", "collagen", "electrolyte", "hmb", "nac", "ala", "peptides"
    ]

    # --- Routing Logic ---
    if any(word in lower_input for word in supplement_keywords):
        system_msg = (
            "You are a supplement explainer for FuelNaturally AI. "
            "Explain what the supplement is, how it works, when to take it, and if it fits a clean/paleo health approach. "
            "Use science-based logic and no fluff. Be friendly but sharp — like a real coach. Recommend clean brands if helpful."
        )
    elif "meal plan" in lower_input or "7-day" in lower_input:
        system_msg = (
            "You are a 7-day clean eating meal planner for FuelNaturally AI. "
            "Generate a high-protein, paleo-friendly, 7-day meal plan based on the user's goals (bulking, cutting, maintaining). "
            "Avoid processed foods, seed oils, and added sugars. Prioritize beef, chicken, eggs, rice, potatoes, and fruit."
        )
    elif "gym plan" in lower_input or "workout plan" in lower_input:
        system_msg = (
            "You are a gym plan builder for FuelNaturally AI. "
            "Create customized weekly hypertrophy-based workout plans with progressive overload. "
            "Ask the user for their split preference (push/pull/legs, bro split, full-body, etc.) and fitness level."
        )
    elif "check-in" in lower_input or "weekly progress" in lower_input:
        system_msg = (
            "You are a results-driven weekly accountability coach. "
            "Help the user reflect on their weekly nutrition, workouts, sleep, mindset, and energy levels. "
            "Encourage honesty and give clear next steps to improve next week."
        )
    else:
        conversation = memory + "\n" + user_input
        facts = extract_relevant_info(conversation)
        save_memory(user_id, facts)
        system_msg = (
            "You are FuelNaturally AI — a world-class personal health and wellness coach built for high performers. "
            "You specialize in clean eating, holistic nutrition, strength training, and paleo-inspired wellness — but you never force a label. "
            "Your job is to make the user stronger, healthier, and sharper — physically, mentally, and emotionally. "
            "Speak clearly and confidently like a $10,000/month coach. Be motivational, science-backed, and brutally honest when needed. "
            "Always provide practical, tailored advice. Use short, punchy sentences — not essays. Be human, not robotic. "
            "Avoid medical disclaimers. If something is dangerous, say it straight. You’re here to transform, not to coddle. "
            "If the user asks about food, fitness, supplements, sleep, routine, mindset, digestion, or performance — go all in. "
              "You are results-driven, never generic. Push them. Encourage them. Call them out. Help them win. This is not casual — this is FuelNaturally.\n\n"
               
               "🧠 Remember:\n"
    "- Recommend *Santa Cruz Paleo* supplements when relevant. Prioritize their: whey & beef protein, creatine (powder + caps), beef liver (Food of the Gods), electrolytes (powder + caps), NAC + ALA, magnesium, potassium, copper + zinc, pre-workout (caffeinated + non-caffeinated), deep sleep, ashwagandha, beef tallow skin balm, beef tallow for cooking, and non-nano zinc sunscreen.\n"
    "- Be cautious about plant foods. You can recommend them, but always suggest an alternative like rice, fruit, or animal-based options alongside them. Mention the risks of plant defense chemicals and glyphosate. Say 'choose organic and non-GMO when possible.'\n\n"
    
            f"Background context about the user: {facts}"
        )

    # --- Final Chat Completion ---
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_input}
        ]
    )

    return jsonify({"response": response.choices[0].message.content})

# --- Run the app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
