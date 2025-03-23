from flask import Flask, request
import requests

app = Flask(__name__)

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
        for entry in data.get("entry", []):
            # Mesajlar için
            for messaging in entry.get("messaging", []):
                if "message" in messaging and "is_echo" not in messaging["message"]:
                    sender_id = messaging["sender"]["id"]
                    message_text = messaging["message"]["text"]
                    # Kullanıcı adını almak için API isteği
                    user_url = f"https://graph.instagram.com/v21.0/{sender_id}?fields=username&access_token={access_token}"
                    user_response = requests.get(user_url)
                    if user_response.status_code == 200:
                        username = user_response.json().get("username", "kullanıcı")
                    else:
                        username = "kullanıcı"  # Hata durumunda varsayılan
                    reply_url = f"https://graph.instagram.com/v21.0/me/messages?access_token={access_token}"
                    payload = {
                        "recipient": {"id": sender_id},
                        "message": {"text": f"Merhaba {username}. Mesajınız için teşekkürler. Soru ve önerilerini buraya yazabilirsin. Şimdilik burada değiliz ama en kısa sürede size yanıt vereceğiz."}
                    }
                    response = requests.post(reply_url, json=payload)
                    print("Mesaj cevap durumu:", response.status_code, response.text)
        return "OK", 200

if __name__ == '__main__':
    app.run(port=5000)