import os
import requests
from dotenv import load_dotenv

load_dotenv()

# RapidAPI üzerinden alınacak anahtar
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# HANGİ APİ'Yİ SEÇECEĞİMİZE GÖRE BU HOST VE ENDPOINT DEĞİŞECEK.
# Şimdilik en popülerlerden biri olan şablonu kullanıyorum.
RAPIDAPI_HOST = "twitter-api45.p.rapidapi.com" 

def fetch_user_tweets(username, limit=5):
    """
    Belirtilen kullanıcının son tweetlerini RapidAPI üzerinden ücretsiz çeker.
    """
    if not RAPIDAPI_KEY:
        print("❌ HATA: RAPIDAPI_KEY bulunamadı. Lütfen .env dosyasına ekleyin.")
        return []
        
    url = f"https://{RAPIDAPI_HOST}/timeline.php"
    
    querystring = {"screenname": username}
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status() 
        
        try:
            data = response.json()
        except Exception:
            print(f"❌ JSON hatası! Status Code: {response.status_code}, Response: {response.text[:100]}")
            return []
        
        extracted_tweets = []
        
        # twitter-api45 dönen veri yapısına göre düzenlenmiştir
        # genelde liste döner veya "timeline" objesi içinde döner.
        timeline_data = data.get('timeline', []) if isinstance(data, dict) else data
        
        for item in timeline_data[:limit]:
            # Retweetleri atla, sadece kendi gönderilerini al
            tweet_text = item.get("text", "")
            tweet_id = item.get("tweet_id") or item.get("tweet_id_str")
            tweet_url = f"https://x.com/{username}/status/{tweet_id}" if tweet_id else None
            
            # Media URL Çekme (Resim veya Video Kapak Resmi)
            media_url = None
            media_obj = item.get("media", {})
            if isinstance(media_obj, dict):
                # Önce resimlere bak
                images = media_obj.get("photo", [])
                if images and len(images) > 0:
                    media_url = images[0].get("media_url_https")
                # Resim yoksa videonun kapak resmine bak
                if not media_url:
                    videos = media_obj.get("video", [])
                    if videos and len(videos) > 0:
                        media_url = videos[0].get("media_url_https")

            if tweet_text:
                extracted_tweets.append({
                    "author": item.get("author", {}).get("name", username.capitalize()),
                    "username": f"@{username}",
                    "author_image": item.get("author", {}).get("avatar"),
                    "text": tweet_text,
                    "media_url": media_url,
                    "tweet_url": tweet_url
                })
                     
        return extracted_tweets
        
    except Exception as e:
        print(f"❌ Tweetler çekilirken hata oluştu: {e}")
        return []

if __name__ == "__main__":
    print("Test amacıyla @fatihaltayli kullanıcısının tweetleri çekiliyor...")
    tweets = fetch_user_tweets("fatihaltayli", limit=2)
    
    if tweets:
        import json
        print(json.dumps(tweets[0], indent=2))
    else:
        print("Boş liste döndü veya hata alındı.")
