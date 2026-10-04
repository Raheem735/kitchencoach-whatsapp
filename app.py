import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Get your tokens from environment variables later
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "kitchen123")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")

@app.route("/", methods=["GET"])
def home():
    return "KitchenCoach WhatsApp Webhook is live!", 200

# This route handles Meta's Webhook Verification Challenge
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Hello world", 200

# This route receives your incoming WhatsApp messages
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.json
    try:
        # Extract incoming message from WhatsApp payload
        message = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_phone = message['from']
        user_text = message['text']['body']

        # Forward text to Gemini API (or process speed dials)
        reply_text = f"KitchenCoach received your message: '{user_text}'. Your inventory and system prompts are active!"

        # Send reply back via WhatsApp Cloud API
        send_whatsapp_message(sender_phone, reply_text)
    except Exception as e:
        print(f"Error processing message: {e}")

    return jsonify({"status": "success"}), 200

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
    requests.post(url, json=headers, json_data=payload) # simplified send

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
