import requests
import threading

from flask import Flask, request, jsonify

from settings import *
from ai_processor import *

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    print('Webhook received, method: ' + request.method)

    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print('Webhook verified successfully')
            return challenge, 200
        else:
            print('Verification failed')
            return 'Verification failed', 403
        
    if request.method == "POST":
        data = request.get_json()
        print('Incoming webhook:', data, flush=True)

        try:
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})

            from_name = 'User Name'
            contacts = value.get('contacts', [])
            if contacts:
                contact = contacts[0];
                from_name = contact.get('profile', {}).get('name', '')

            print(f'Message sender: {from_name}')

            messages = value.get('messages', [])

            if messages:
                msg = messages[0]
                from_number = msg.get('from')
                msg_type = msg.get('type')

                if msg_type == 'text':
                    text = msg.get('text', {}).get('body', '')
                    print(f'Message from {from_number}: {text}')

                    threading.Thread(
                        target=handle_incoming_message,
                        args=(from_number, from_name, text),
                        daemon=True,
                    ).start()
                else:
                    print(f'Received {msg_type} message from {from_number}')

        except Exception as e:
            print(f'Error processing webhook: {e}')

        return 'EVENT_RECEIVED', 200

def handle_incoming_message(from_number, from_name, text):

# To test Whatsapp message sending only
#    reply = process_message(from_name, 'Write a quatrain about vacation')
#    send_reply(your_phone_number, reply)

    reply = process_message(from_name, text)
    send_reply(from_number, reply)
    

def send_reply(to, text):

    print(f'Replying to {to}: {text}')

    url = f'https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages'

    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }

    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {
            'body': text
        }
    }

    resp = requests.post(url, headers=headers, json=payload)
    print(f'Message sent: {resp.status_code} - {resp.text}')
    return resp


if __name__ == '__main__':
    if not WHATSAPP_TOKEN:
        print('Warning: WHATSAPP_ACCESS_TOKEN not set')
    if not PHONE_NUMBER_ID:
        print('Warning: WHATSAPP_PHONE_NUMBER_ID not set')
    
    print(f'Verify token: {VERIFY_TOKEN}')
    print(f'Starting Flask server on 0.0.0.0:{PORT}...')

# To test AI model only
#    reply = process_message('Mike', 'Write a quatrain about vacation')
#    print(reply)

    app.run(host='0.0.0.0', port=PORT, debug=True)
