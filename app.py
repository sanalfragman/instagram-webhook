from flask import Flask, request
import requests
import time
import logging
import os
import json
import threading

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

def send_delayed_message(sender_id, access_token, message_text):
    time.sleep(15)  # 15 saniye bekle
    if sender_id not in active_chats or active_chats[sender_id] == 0:
        reply_url = f"https://graph.instagram.com/v21.0/me/messages?access_token={access_token}"
        payload = {
            "recipient": {"id": sender_id},
            "message": {"text": "Mesajınız için teşekkürler. Soru ve önerilerinizi buraya yazabilirsiniz. En kısa sürede size yanıt vereceğiz."}
        }
        response = requests.post(reply_url, json=payload)
        logger.info(f"Gecikmeli mesaj durumu: {response.status_code} {response.text}")
        if response.status_code == 200:
            active_chats[sender_id] = time.time()  # Gecikmeli cevap başarılıysa aktif sohbet başlat
            save_active_chats(active_chats)

active_chats = load_active_chats()
access_token = INITIAL_TOKEN

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    global active_chats, access_token
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
                    if sender_id in active_chats and (time.time() - active_chats[sender_id]) < 3600:
                        logger.info(f"{sender_id} ile aktif sohbet, otomatik cevap verilmedi")
                        continue
                    
                    message_text = messaging["message"]["text"]
                    logger.info(f"Mesaj: {message_text}")
                    user_url = f"https://graph.instagram.com/v21.0/{sender_id}?fields=username&access_token={access_token}"
                    user_response = requests.get(user_url)
                    if user_response.status_code == 200:
                        username = user_response.json().get("username", "kullanıcı")
                    else:
                        username = "kullanıcı"
                    
                    reply_url = f"https://graph.instagram.com/v21.0/me/messages?access_token={access_token}"
                    payload = {
                        "recipient": {"id": sender_id},
                        "message": {"text": "Mesajınız için teşekkürler. Soru ve önerilerinizi buraya yazabilirsiniz. En kısa sürede size yanıt vereceğiz."}
                    }
                    response = requests.post(reply_url, json=payload)
                    logger.info(f"Mesaj cevap durumu: {response.status_code} {response.text}")
                    
                    if response.status_code == 200:
                        active_chats[sender_id] = time.time()  # İlk cevap başarılıysa aktif sohbet başlat
                        save_active_chats(active_chats)
                    else:
                        logger.info(f"İlk mesaj başarısız, gecikmeli gönderim başlatılıyor: {sender_id}")
                        threading.Thread(target=send_delayed_message, args=(sender_id, access_token, message_text), daemon=True).start()
        
        return "OK", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)