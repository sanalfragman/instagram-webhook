from flask import Flask, request
import requests
import time
import json
import os

app = Flask(__name__)

CHAT_FILE = "active_chats.json"

def load_active_chats():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    print("Dosya yok, yeni active_chats oluşturuluyor.")
    return {}

def save_active_chats(chats):
    with open(CHAT_FILE, "w") as f:
        json.dump(chats, f)
    print(f"Active chats dosyaya kaydedildi: {chats}")

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = "Yby-2020"
        if request.args.get('hub.verify_token') == verify_token:
            return request.args.get('hub.challenge')
        return "Doğrulama başarısız", 403
    
    elif request.method == 'POST':
        data = request.json
        print("Gelen veri:", data)
        access_token = "IGAARDZCufpcfZABZAE04SUg2Tkd2R0FHZAGd2LThxa3FxQnBlcFZA2ZATNoZATJqNE1TY1RoZAVdQNXJwZAzdfU1MtSFRqMWJWYl8waHluSGE1RVNPeE9POXJncEZAsQ2ttM0ZAvUjl4U1JBU00yVl84ZAnlrb2VaWUxPR2gyczE2OGI4NU9McwZDZD"
        
        active_chats = load_active_chats()
        
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                print(f"Sender ID: {sender_id}")
                
                # Senin gönderdiğin mesaj mı?
                if "message" in messaging and messaging.get("message", {}).get("is_echo"):
                    active_chats[sender_id] = time.time()
                    save_active_chats(active_chats)
                    print(f"{sender_id} için aktif sohbet işaretlendi.")
                    continue
                
                # Kullanıcının mesajı mı?
                if "message" in messaging and "is_echo" not in messaging["message"]:
                    if sender_id in active_chats and (time.time() - active_chats[sender_id]) < 3600:
                        print(f"{sender_id} ile aktif sohbet, otomatik cevap verilmedi.")
                        continue
                    
                    message_text = messaging["message"]["text"]
                    print(f"Mesaj: {message_text}")
                    user_url = f"https://graph.instagram.com/v21.0/{sender_id}?fields=username&access_token={access_token}"
                    user_response = requests.get(user_url)
                    if user_response.status_code == 200:
                        username = user_response.json().get("username", "kullanıcı")
                    else:
                        username = "kullanıcı"
                    
                    reply_url = f"https://graph.instagram.com/v21.0/me/messages?access_token={access_token}"
                    payload = {
                        "recipient": {"id": sender_id},
                        "message": {"text": f"Merhaba {username}. Mesajınız için teşekkürler. Soru ve önerilerini buraya yazabilirsin. Şimdilik burada değiliz ama en kısa sürede size yanıt vereceğiz."}
                    }
                    response = requests.post(reply_url, json=payload)
                    print("Mesaj cevap durumu:", response.status_code, response.text)
        
        return "OK", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)