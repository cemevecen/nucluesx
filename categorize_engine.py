import os
from google import genai
from dotenv import load_dotenv
from database import init_db, save_tweet, tweet_exists
import time
from twitter_scraper import fetch_user_tweets

# .env dosyasındaki anahtarları yükler
load_dotenv()

# Veritabanını kullanıma hazır hale getir (Yoksa oluşturur)
init_db()

# Yeni Google GenAI kütüphanesi başlatımı
# Cloud ortamında (Streamlit) secrets'tan okumak için düzenlendi
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

try:
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        client = None
        print("⚠️ Uyarı: GEMINI_API_KEY bulunamadı.")
except Exception as e:
    client = None
    print(f"❌ NucleusX Gemini Client Hatası: {e}")

def categorize_tweet(tweet_text):
    """Tweet metnini alır ve Gemini yapay zekası yardımıyla kategorize eder."""
    
    if not client:
        print("⚠️ Gemini Client kapalı, 'Diğer' atanıyor.")
        return "Diğer"
    
    prompt = f"""
    Sen, NucleusX gibi bir haber toplayıcı (aggregator) için çalışan baş editörsün.
    Aşağıdeki tweet metnini oku ve onu bu 8 kategoriden sadece BİRİNE yerleştir:
    Kategoriler: Ekonomi, Finans, Spor, Teknoloji, Eğlence, Müzik, Dünya, Ülke Gündemi
    
    Eğer tweet alakasızsa veya anlaşılmıyorsa "Diğer" de.
    SADECE kategorinin adını yaz. Başka hiçbir açıklama yapma.
    
    Tweet: "{tweet_text}"
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        res = response.text.strip()
        # AI bazen köşeli parantez veya nokta ekleyebilir, temizleyelim
        return res.replace("[", "").replace("]", "").replace(".", "").strip()
    except Exception as e:
        print(f"⚠️ Gemini hatası: {e}")
        return "Bilinmeyen Kategori"

def run_categorization_process():
    """Tüm hedef hesaplardan tweetleri çeker, kategorize eder ve kaydeder."""
    target_accounts = [
        "fatihaltayli", "ozgurdemirtas", "yagosabuncuoglu", "shiftdelete", 
        "boxofficeturkey", "MuzikOnair", "trthaber", "pusholder", "ajans_muhbir"
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
            
            # 2. Rate Limiting (Ücretsiz Planı Korumak İçin)
            time.sleep(1) 

            # Yapay Zeka Devreye Girer
            kategori = categorize_tweet(tweet['text'])

            # Veritabanına kaydet
            save_tweet(tweet['author'], tweet['username'], tweet['text'], kategori)
            yield f"✅ {tweet['username']}: [{kategori}]"
    
    print("\n" + "-" * 50)
    print("✅ Analiz Tamamlandı! Tüm veriler NucleusX veritabanına işlendi.")

if __name__ == "__main__":
    init_db()
    for status in run_categorization_process():
        print(status)
