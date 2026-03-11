import os
from google import genai
from dotenv import load_dotenv
from database import init_db, save_tweet, tweet_exists
import time
import requests
from twitter_scraper import fetch_user_tweets

# .env dosyasındaki anahtarları yükler
load_dotenv()

# Veritabanını kullanıma hazır hale getir (Yoksa oluşturur)
init_db()

# API Anahtarları
api_key_gemini = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
api_key_groq = os.getenv("GROQ_API_KEY")
api_key_mistral = os.getenv("MISTRAL_API_KEY")

# Gemini Client
try:
    if api_key_gemini:
        client_gemini = genai.Client(api_key=api_key_gemini)
    else:
        client_gemini = None
except Exception:
    client_gemini = None

def categorize_with_groq(text):
    """Gemini dursa bile Groq üzerinden Llama-3 ile analiz yapar (Ücretsiz ve Hızlı)."""
    if not api_key_groq:
        return None
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key_groq}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Categorize this news/tweet into ONE of these: Ekonomi, Finans, Spor, Teknoloji, Eğlence, Müzik, Dünya, Ülke Gündemi. Respond with ONLY the category name.\n\nText: {text}"
    
    # 8B modeli çok daha hızlıdır ve kotası daha yüksektir, kategori için yeterlidir.
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            res = response.json()['choices'][0]['message']['content'].strip().replace(".", "")
            if res in ["Ekonomi", "Finans", "Spor", "Teknoloji", "Eğlence", "Müzik", "Dünya", "Ülke Gündemi"]:
                return res
        elif response.status_code == 429: # Rate limit dursa da sistem anahtar kelimeye geçmeli
             return None
        return None
    except Exception:
        return None

def categorize_with_mistral(text):
    """Mistral AI üzerinden analiz yapar (3. Yedek)."""
    if not api_key_mistral:
        return None
        
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key_mistral}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Categorize into ONE: Ekonomi, Finans, Spor, Teknoloji, Eğlence, Müzik, Dünya, Ülke Gündemi. Respond with ONLY the category name.\n\nText: {text}"
    
    data = {
        "model": "open-mistral-7b", 
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            res = response.json()['choices'][0]['message']['content'].strip().replace(".", "")
            if res in ["Ekonomi", "Finans", "Spor", "Teknoloji", "Eğlence", "Müzik", "Dünya", "Ülke Gündemi"]:
                return res
        return None
    except Exception:
        return None

def get_fallback_category(text):
    """AI hata verdiğinde anahtar kelimelerle kategori tahmini yapar."""
    text = text.lower()
    keywords = {
        "Ekonomi": ["dolar", "euro", "faiz", "enflasyon", "zam", "asgari", "maai", "bakanlık", "vergi"],
        "Finans": ["borsa", "hisse", "temettü", "kripto", "bitcoin", "altın", "btc", "eth", "yatırım"],
        "Spor": ["gol", "maç", "skor", "futbol", "basketbol", "fenerbahçe", "galatasaray", "beşiktaş", "transfer"],
        "Teknoloji": ["iphone", "apple", "android", "yazılım", "yapay zeka", "ai", "internet", "google", "çip"],
        "Eğlence": ["film", "dizi", "netflix", "sinema", "oyuncu", "magazin", "ünlü"],
        "Müzik": ["şarkı", "albüm", "konser", "klip", "single", "sanatçı", "spotify"],
        "Dünya": ["savaş", "abd", "rusya", "israil", "gazze", "nato", "avrupa", "bm"],
        "Ülke Gündemi": ["siyaset", "seçim", "meclis", "parti", "istifa", "belediye", "trt", "aa"]
    }
    
    for cat, words in keywords.items():
        if any(word in text for word in words):
            return cat
    return "Ülke Gündemi" # Varsayılan kategori

def categorize_tweet(tweet_text):
    """
    Kategori belirleme zinciri: 
    1. Gemini (Ana) -> 2. Groq (Llama-3) -> 3. Mistral -> 4. Anahtar Kelime
    """
    
    # 1. Aşama: Gemini Dene
    if client_gemini:
        try:
            prompt = f"Metni şu kategorilerden birine yerleştir: Ekonomi, Finans, Spor, Teknoloji, Eğlence, Müzik, Dünya, Ülke Gündemi. SADECE kategorinin ismini yaz.\nMetin: {tweet_text}"
            response = client_gemini.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            res = response.text.strip().replace("[", "").replace("]", "").replace(".", "")
            if res in ["Ekonomi", "Finans", "Spor", "Teknoloji", "Eğlence", "Müzik", "Dünya", "Ülke Gündemi"]:
                return res
        except Exception:
            pass

    # 2. Aşama: Groq (Llama-3) Dene
    res_groq = categorize_with_groq(tweet_text)
    if res_groq:
        return res_groq

    # 3. Aşama: Mistral Dene
    res_mistral = categorize_with_mistral(tweet_text)
    if res_mistral:
        return res_mistral
        
    # 4. Aşama: Anahtar Kelime (En Son Çare)
    return get_fallback_category(tweet_text)

def run_categorization_process():
    """Tüm hedef hesaplardan tweetleri çeker, kategorize eder ve kaydeder."""
    target_accounts = [
        # Ülke Gündemi
        "pusholder", "ajans_muhbir",
        # Dünya
        "bbcturkce", "euronews_tr",
        # Ekonomi
        "ozgurdemirtas", "temelanaliz",
        # Finans
        "borsagundem", "ParaAnaliz",
        # Teknoloji
        "shiftdelete", "webteknoloji",
        # Spor
        "yagosabuncuoglu", "sporx",
        # Eğlence
        "boxofficeturkey", "raninitv",
        # Müzik
        "MuzikOnair", "PopBizde"
    ]
    
    print("-" * 50)
    print("🚀 NucleusX AI Haber Sınıflandırıcı Motoru Başlıyor...")
    print("-" * 50)
    
    for username in target_accounts:
        # Streamlit'e o an taranan hesabı bildirelim
        yield f"📡 {username} hesabından tweetler çekiliyor..."
        
        tweets = fetch_user_tweets(username, limit=5) # 10 çok yavaşlattığı için 5 ideal
        
        if not tweets:
            print(f"🔍 {username} için yeni tweet bulunamadı veya bir hata oluştu.")
            continue
            
        for tweet in tweets:
            # 1. Mükerrer Kontrolü (İçeriğin ilk 50 karakteri üzerinden daha esnek kontrol)
            # Sadece tam eşleşme yerine kullanıcı adı + kısa özet kontrolü
            if tweet_exists(tweet['username'], tweet['text']):
                print(f"⏩ {tweet['username']} için bu tweet zaten işlenmiş, atlanıyor.")
                continue

            print(f"\n👤 GÖNDEREN: {tweet['author']} ({tweet['username']})")
            print(f"📝 TWEET: {tweet['text'][:100]}...") # Uzun tweetleri keserek basıyoruz
            
            # 2. Rate Limiting (KOTA KORUMASI: SADECE ÜCRETSİZ PLANLAR)
            # Gemini Free 15 RPM / Groq Free 30 RPM limitlerini aşmamak için 
            # 4 saniye bekleme (Saniyede 15 istekten azına denk gelir). 
            # Bu sayede 'Maliyet Sıfır, Kesintisizlik Tam' olur.
            time.sleep(4) 

            # Yapay Zeka Devreye Girer
            kategori = categorize_tweet(tweet['text'])

            # Veritabanına kaydet (Resim varsa ekle)
            save_tweet(tweet['author'], tweet['username'], tweet['text'], kategori, media_url=tweet.get('media_url'))
            yield f"✅ {tweet['username']}: [{kategori}]"
    
    print("\n" + "-" * 50)
    print("✅ Analiz Tamamlandı! Tüm veriler NucleusX veritabanına işlendi.")

if __name__ == "__main__":
    init_db()
    for status in run_categorization_process():
        print(status)
