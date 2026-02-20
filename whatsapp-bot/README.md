# WhatsApp AI Chatbot (Cloud API + Flask)

## Overview

A minimal Flask-based service that connects WhatsApp Cloud API with an AI backend. Incoming WhatsApp messages are received via a Meta webhook endpoint, processed using a custom prompt, and replied to asynchronously via the WhatsApp Cloud API.  

Webhook setup guide: https://developers.facebook.com/docs/graph-api/webhooks/getting-started/

## Setup

1. Create a Meta app and enable the WhatsApp Cloud API in [Meta for Developers](https://developers.facebook.com/)

2. Obtain:
    - WhatsApp **Access Token**
    - **Phone Number ID**
    - **Verify Token** (a string you define and reuse in both code and Meta Webhooks config).

3. Configure environment variables (e.g., in `.env`):
    - `WHATSAPP_VERIFY_TOKEN`
    - `WHATSAPP_ACCESS_TOKEN`
    - `WHATSAPP_PHONE_NUMBER_ID`
    - `PORT` (e.g. `5000`)
    - `OPENAI_API_KEY` (or compatible AI/LLM provider key).
4. Install dependencies:

```bash
pip install flask requests python-dotenv langchain-core
```

Alternatively, you can install all required packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

5. Run the Flask app:

```bash
python app.py
```

The app exposes `/webhook` with GET (verification) and POST (message handling).

6. Start ngrok (or another tunneling tool) for your Flask port:

```bash
ngrok http 5000
```

7. In Meta Developer Dashboard → WhatsApp → Configuration → Webhooks:
    - Set **Callback URL** to `https://<your-ngrok-id>.ngrok-free.app/webhook`
    - Set **Verify Token** to `WHATSAPP_VERIFY_TOKEN`
    - Click **Verify and Save**
    - Subscribe to `messages`.

## How it works

- **GET `/webhook`**
Meta calls this once during webhook verification. The app checks `hub.mode`, `hub.verify_token`, and returns `hub.challenge` if the verify token matches, otherwise responds with 403.

- **POST `/webhook`**
Meta sends incoming WhatsApp messages as JSON. The app:
    - Extracts sender name, phone number, and text from `entry[0].changes[0].value`.
    - Starts a background thread so that the HTTP response is returned immediately.
    - Returns `EVENT_RECEIVED` with HTTP 200.

```python
threading.Thread(
    target=handle_incoming_message,
    args=(from_number, from_name, text),
    daemon=True,
).start()
```

- **`handle_incoming_message(from_number, from_name, text)`**
    - Calls `process_message(from_name, text)` – your AI integration, which uses `main_prompt` from `prompts.py` to build the final prompt.
    - Sends the generated reply to the user with `send_reply(from_number, reply)`.

- **`send_reply(to, text)`**
Sends a text reply via WhatsApp Cloud API:

```http
POST https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages
Authorization: Bearer WHATSAPP_ACCESS_TOKEN
Content-Type: application/json
```

with the following JSON body:

```json
{
  "messaging_product": "whatsapp",
  "to": "<phone>",
  "type": "text",
  "text": { "body": "<reply>" }
}
```

## Testing notes (Meta / WhatsApp policy)

Meta’s WhatsApp Cloud API has specific limits for **test phone numbers and allowed recipients** in development mode:

- You can only send messages to:
    - the official test phone number, and
    - up to 5 “allowed” phone numbers you configure in the “Getting Started” section of WhatsApp Cloud API.
- You cannot use any arbitrary personal WhatsApp account; test traffic must involve the test number and allowlisted recipients, and many flows are driven from the Meta dashboard tools.

Official docs (policy and behavior):

- WhatsApp Business Platform: Getting Started – https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- Webhooks – https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/

Because of these constraints, you typically **cannot test “full end-to-end” flows purely from a random personal WhatsApp client**. Instead, you test the logic in **separate pieces**, for which the code already contains commented sections:

1. **Test WhatsApp sending only**
In `handle_incoming_message` there is a commented block:

```python
# To test Whatsapp message sending only
# reply = process_message(from_name, 'Write a quatrain about vacation')
# send_reply(your_phone_number, reply)
```

Use this with your allowlisted test phone number to confirm that outbound messages work, without depending on real inbound webhooks.

2. **Test AI logic only**
In the `__main__` section there is a commented snippet:

```python
# To test AI model only
# reply = process_message('Mike', 'Write a quatrain about vacation')
# print(reply)
```

This lets you validate prompts and AI responses locally, without WhatsApp or Meta.

3. **Test full flow (Dashboard-driven)**
After verifying sending and AI separately:
    - Use Meta’s dashboard test tools (“Send message”, “Test webhook”, etc.) to trigger webhook POST calls.
    - Ensure that the webhook receives payloads.
    - The background thread calls the AI.
    - `send_reply` successfully posts replies back to WhatsApp Cloud API.

## See also

- https://stackoverflow.com/questions/40989671/background-tasks-in-flask  
- https://stackoverflow.com/questions/73083742/how-to-run-a-function-in-the-background-of-flask-app


