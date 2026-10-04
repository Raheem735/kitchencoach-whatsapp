import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "kitchen123")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")

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
    try:
        message = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_phone = message['from']
        user_text = message['text']['body']

        # Call Gemini API with KitchenCoach persona
        reply_text = call_gemini_kitchencoach(user_text)

        # Send reply back via WhatsApp Cloud API
        send_whatsapp_message(sender_phone, reply_text)
    except Exception as e:
        print(f"Error processing message: {e}")

    return jsonify({"status": "success"}), 200

def call_gemini_kitchencoach(prompt):
    # Sends user text to Gemini API using your AI Studio key
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": f"You are KitchenCoach, a personal Kitchen Manager, Chef, and Calorie-Deficit Nutritionist. User says: {prompt}"}]
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
