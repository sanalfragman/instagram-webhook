from flask import Flask, request
import requests
import time
import logging
import os
import json

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

CHAT_FILE = "/tmp/active_chats.json"
MY_ID = "17841473301044042"
INITIAL_TOKEN = "IGAARDZCufpcfZABZAE04SUg2Tkd2R0FHZAGd2LThxa3FxQnBlcFZA2ZATNoZATJqNE1TY1RoZAVdQNXJwZAzdfU1MtSFRqMWJWYl8waHluSGE1RVNPeE9POXJncEZAsQ2ttM0ZAvUjl4U1JBU00yVl84ZAnlrb2VaWUxPR2gyczE2OGI4NU9McwZDZD"

def load_active_chats():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    logger.info("Dosya yok, yeni active_chats oluşturuluyor.")
    return {}

def save_active_chats(chats):
    with open(CHAT_FILE, "w") as f:
        json.dump(chats, f)
    logger.info(f"Active chats dosyaya kaydedildi: {chats}")

def send_auto_reply(sender_id, access_token):
    reply_url = f"https://graph.instagram.com/v21.0/me/messages?access_token={access_token}"
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": "Mesajınız için teşekkürler. Soru ve önerilerinizi buraya yazabilirsiniz. En kısa sürede size yanıt vereceğiz."}
    }
    response = requests.post(reply_url, json=payload)
    logger.info(f"Otomatik cevap durumu: {response.status_code} {response.text}")
    if response.status_code == 200:
        active_chats[sender_id] = time.time()
        save_active_chats(active_chats)

def check_last_message(access_token):
    conv_url = f"https://graph.instagram.com/v21.0/me/conversations?fields=participants,messages&access_token={access_token}"
    conv_response = requests.get(conv_url)
    if conv_response.status_code != 200:
        logger.error(f"Konuşma alma hatası: {conv_response.status_code} {conv_response.text}")
        return
    
    conversations = conv_response.json().get("data", [])
    if not conversations:
        logger.info("Hiç konuşma yok.")
        return
    
    latest_conv = conversations[0]
    participants = latest_conv["participants"]["data"]
    sender_id = next(p["id"] for p in participants if p["id"] != MY_ID)
    last_message = latest_conv["messages"]["data"][0]
    message_time = int(last_message["timestamp"]) / 1000  # Milisaniyeyi saniyeye çevir
    
    # Son mesaj 1 dk içinde gelmiş ve cevaplanmamışsa
    if (time.time() - message_time) <= 60 and sender_id not in active_chats:
        logger.info(f"Son mesaj 1 dk içinde, cevaplanmamış: {sender_id}")
        send_auto_reply(sender_id, access_token)

active_chats = load_active_chats()
access_token = INITIAL_TOKEN
first_run = True  # Sistem uyandığında ilk çalıştırmayı işaretler

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    global active_chats, access_token, first_run
    logger.info("Webhook isteği alındı")
    
    if request.method == 'GET':
        verify_token = "Yby-2020"
        if request.args.get('hub.verify_token') == verify_token:
            logger.info("GET doğrulaması başarılı")
            return request.args.get('hub.challenge')
        logger.info("GET doğrulaması başarısız")
        return "Doğrulama başarısız", 403
    
    elif request.method == 'POST':
        data = request.json
        logger.info(f"Gelen veri: {data}")
        
        processed = False
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                recipient_id = messaging["recipient"]["id"]
                logger.info(f"Sender ID: {sender_id}, Recipient ID: {recipient_id}")
                
                if "message" in messaging and messaging.get("message", {}).get("is_echo"):
                    if sender_id == MY_ID:
                        active_chats[recipient_id] = time.time()
                        save_active_chats(active_chats)
                        logger.info(f"{recipient_id} için aktif sohbet işaretlendi (senin mesajın)")
                    continue
                
                if "message" in messaging and "is_echo" not in messaging["message"]:
                    processed = True
                    if sender_id in active_chats and (time.time() - active_chats[sender_id]) < 3600:
                        logger.info(f"{sender_id} ile aktif sohbet, otomatik cevap verilmedi")
                        continue
                    
                    message_text = messaging["message"]["text"]
                    logger.info(f"Mesaj: {message_text}")
                    send_auto_reply(sender_id, access_token)
        
        # Sistem uyandığında (ilk çalıştırma) ve mesaj işlenemediyse son mesajı kontrol et
        if first_run and not processed:
            logger.info("Sistem uyandı, son mesaj kontrol ediliyor.")
            check_last_message(access_token)
            first_run = False  # İlk çalıştırmadan sonra bayrağı kapat
        
        return "OK", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)