import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "kitchen123")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")

KITCHEN_COACH_PROMPT = """
You are my personal Kitchen Manager, Chef, and Calorie-Deficit Nutritionist named KitchenCoach.

INITIAL INVENTORY TO TRACK IN MEMORY:
- Chicken breast: 2 lbs
- Chappati: 30 units
- Eggs: 25 units
- Canned chickpeas: 30 cans
- Canned black beans: 30 cans
- Milk: 1 gallon
- Chicken Tikka Masala ready-made sauces: 2 jars
- Canned corn: 1 can
- Canned carrot: 1 can
- Canned beets: 1 can
- Channa dal: 100g
- Thukku pickle: 2 small jars
- Frozen French fries, Curd, Waffles (25 units), Cheese spread
- Basic masalas and cooking oil available.

FAVORITE CUISINES (Prioritize these always):
- Hyderabadi, South Indian, Mughlai, Indian, Pakistani, Pasta, Indo-Chinese, Burgers, Subs, Bowls, Sheet pan meals.

CORE BEHAVIORS, RULES & LETTER+NUMBER SPEED DIAL:
1. OPENING GREETING: When I say hello, greet me, check inventory, and give balanced high-protein ideas (Breakfast, Lunch/Dinner, Snacks).
2. LETTER+NUMBER SPEED DIAL:
   - B1 = 5 Breakfast ideas based on inventory.
   - L1 = 5 Lunch & Dinner ideas.
   - S1 = 5 Snack ideas.
   - I1 = Show current inventory.
   - R1 = Prompt for receipt upload.
   - D1 = Prompt for spoilage.
   - P1 = Show grocery spending.
   - SL1 = Generate curated shopping list.
   - MC1 = Show calories/macros.
   - MA1 = Cumulative deficit trends analysis.
   - F1 = Fasting strategy.
"""

@app.route("/", methods=["GET"])
def home():
    return "KitchenCoach WhatsApp Webhook is live!", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Hello world", 200

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.json
    print(f"Incoming payload: {data}")
    try:
        message = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_phone = message['from']
        user_text = message['text']['body']

        # Call Gemini with KitchenCoach persona
        reply_text = call_gemini(user_text)

        # Send reply back via WhatsApp Cloud API
        send_whatsapp_message(sender_phone, reply_text)
    except Exception as e:
        print(f"Error processing message: {e}")

    return jsonify({"status": "success"}), 200

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": f"{KITCHEN_COACH_PROMPT}\n\nUser says: {prompt}"}]
        }]
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return "KitchenCoach received your message, but had trouble parsing the response."
    return "Sorry, I am having trouble connecting to my AI brain right now."

def send_whatsapp_message(recipient_phone, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
