import os
import re
from google import genai
from dotenv import load_dotenv
from database import init_db, save_tweet, tweet_exists
import time
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from twitter_scraper import fetch_user_tweets

# .env dosyasındaki anahtarları yükler
load_dotenv()

# API Anahtarları
api_key_gemini = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
api_key_groq = os.getenv("GROQ_API_KEY")
api_key_mistral = os.getenv("MISTRAL_API_KEY")

# Gemini Client
# try:
#     if api_key_gemini:
#         client_gemini = genai.Client(api_key=api_key_gemini)
#     else:
#         client_gemini = None
# except Exception:
#     client_gemini = None
client_gemini = None # AI Temporarily Disabled

def categorize_with_groq(text):
    """Gemini dursa bile Groq üzerinden Llama-3 ile analiz yapar (Ücretsiz ve Hızlı)."""
    if not api_key_groq:
        return None
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key_groq}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Bir haber editörü gibi davranarak metni SADECE bir kategoriye ata: Ekonomi, Spor, Teknoloji, Eğlence, Müzik, Dünya, Türkiye.

Rehber:
- EKONOMİ: Borsa, şirket, ihale, döviz, zam, vergi, banka.
- SPOR: Futbol, basketbol, transfer, kulüp başkanları (Sadettin Saran, Ali Koç) ve maçlar.
- TEKNOLOJİ: AI, yazılım, cihaz, bilim.

SADECE kategori adını yaz. Başka hiçbir şey yazma.

Haber: {text}"""
    
    data = {
        "model": "llama-3.1-8b-instant", # Daha yeni Llama 3.1 modelini dene
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            res = response.json()['choices'][0]['message']['content'].strip()
            # Şık cevapları temizle (Örn: "Category: Spor" -> "Spor")
            for cat in ["Ekonomi", "Spor", "Teknoloji", "Eğlence", "Müzik", "Dünya", "Türkiye"]:
                if cat in res:
                    return cat
        return None
    except Exception:
        return None

def generate_topic_tag(text):
    """
    Haber metni için KURAL tabanlı konu etiketi üretir (AI Kapalı).
    """
    text = text.strip()
    # 1. Eğer metinde #etiket varsa onu kullan
    hashtags = re.findall(r'#(\w+)', text)
    if hashtags:
        return f"#{hashtags[0].upper()}"
    
    # 2. Üst tırnak içindeki kelimeleri bul (Önemli özneler genelde buradadır)
    quotes = re.findall(r'["\'](.*?)["\']', text)
    if quotes and len(quotes[0]) > 3:
        tag = quotes[0].upper().replace(" ", "_")[:20]
        return f"#{tag}"
        
    # 3. İlk iki kelimeyi al (Basit bir çözüm)
    words = [w for w in text.split() if len(str(w)) > 3 and not str(w).startswith('http')]
    if len(words) >= 2:
        tag = f"{words[0]}_{words[1]}".upper().replace(".", "").replace(",", "")
        return f"#{str(tag)[:20]}"
        
    return "#DETAY"

def categorize_with_mistral(text):
    """Mistral AI üzerinden analiz yapar (3. Yedek)."""
    if not api_key_mistral:
        return None
        
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key_mistral}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Kategori seç (Ekonomi, Spor, Teknoloji, Eğlence, Müzik, Dünya, Türkiye). SADECE kategori adını yaz. Metin: {text}"
    
    data = {
        "model": "mistral-tiny", 
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            res = response.json()['choices'][0]['message']['content'].strip()
            for cat in ["Ekonomi", "Spor", "Teknoloji", "Eğlence", "Müzik", "Dünya", "Türkiye"]:
                if cat in res:
                    return cat
        return None
    except Exception:
        return None

# -----------------------------------------------------------------------------
# SOURCE BASED MAPPING (V40.0 - AI ELIMINATED)
# -----------------------------------------------------------------------------
SOURCE_MAPPING = {
    # Türkiye / Gündem
    "pusholder": "Türkiye", "ajans_muhbir": "Türkiye", "haskologlu": "Türkiye", 
    "darkwebhaber": "Türkiye", "solcugazete": "Türkiye", "haberreport": "Türkiye", 
    "beehaber": "Türkiye", "aykiricomtr": "Türkiye", "bpthaber": "Türkiye", "haber": "Türkiye",
    "yirmi3derece": "Türkiye", "onediopolitik": "Türkiye", "t24comtr": "Türkiye",

    # Ekonomi
    "ozgurdemirtas": "Ekonomi", "temelanaliz": "Ekonomi", "ekonomimcom": "Ekonomi", 
    "econofia": "Ekonomi", "borsagundem": "Ekonomi", "paraanaliz": "Ekonomi", 
    "investingtr": "Ekonomi", "paramevzu": "Ekonomi", "dunya_gazetesi": "Ekonomi", "bloomberght": "Ekonomi",
    "mahfiegilmez": "Ekonomi", "bloomberg_tr": "Ekonomi", "ekonomimaus": "Ekonomi",

    # Spor
    "yagosabuncuoglu": "Spor", "sporx": "Spor", "ntvspor": "Spor", 
    "beinsports_tr": "Spor", "asmarcatr": "Spor", "fanatikcomtr": "Spor", 
    "fotomac": "Spor", "trtspor": "Spor", "mackolik": "Spor", "trendbasket": "Spor",
    "ertansuzgun": "Spor", "nexustransfer": "Spor", "skorercom": "Spor",

    # Teknoloji
    "shiftdelete": "Teknoloji", "webteknoloji": "Teknoloji", "donanimhaber": "Teknoloji", 
    "teknoseyir": "Teknoloji", "hakkialkan": "Teknoloji", "mesutcevik": "Teknoloji", 
    "barisozcan": "Teknoloji", "gdh_digital": "Teknoloji", "logdergisi": "Teknoloji", "bilim_teknik": "Teknoloji",
    "technopatnet": "Teknoloji", "hardwareplus": "Teknoloji", "pc_hocasi": "Teknoloji",

    # Dünya
    "bbcturkce": "Dünya", "euronews_tr": "Dünya", "dw_turkce": "Dünya", 
    "voaturkce": "Dünya", "independentturk": "Dünya", "sputnik_tr": "Dünya", 
    "anadoluajansi": "Dünya", "trthaber": "Dünya", "ntv": "Dünya", "ensonhaber": "Dünya",
    "trtdunya": "Dünya", "aljazeera_turk": "Dünya", "ajplus": "Dünya",

    # Eğlence / Magazin
    "boxofficeturkey": "Eğlence", "raninitv": "Eğlence", "birsenaltuntas1": "Eğlence", 
    "tokyophoner": "Eğlence", "magazingozi": "Eğlence", "onedio": "Eğlence", 
    "listelist": "Eğlence", "nocontexttr": "Eğlence", "capsmerkezi": "Eğlence", "dizilah": "Eğlence",
    "magazin_d": "Eğlence", "magazinkolik": "Eğlence", "snobmagazin": "Eğlence",

    # Müzik
    "muzikonair": "Müzik", "popbizde": "Müzik", "murekkephaber": "Müzik", 
    "kultur_sanat": "Müzik", "netdmuzik": "Müzik", "powerapptr": "Müzik", 
    "kralpop": "Müzik", "joyturk": "Müzik", "radyofenomen": "Müzik", "backstagemuzik": "Müzik",
    "trtmuzik": "Müzik", "powerturk": "Müzik", "radyoviva": "Müzik"
}

def populate_sources_table():
    """SOURCE_MAPPING sözlüğünü veritabanına taşır (Tek seferlik)."""
    from database import upsert_source
    for user, cat in SOURCE_MAPPING.items():
        upsert_source(user, cat)
    print("✅ Sabit kaynak listesi veritabanına işlendi.")

def get_fallback_category(text, username=None):
    """Haber kaynağına veya anahtar kelimelere göre kategori tahmini yapar (AI Off)."""
    if username and username.lower() in SOURCE_MAPPING:
        return SOURCE_MAPPING[username.lower()]

    text = text.lower()
    keywords = {
        "Ekonomi": ["dolar", "euro", "faiz", "enflasyon", "zam", "asgari", "maaş", "vergi", "borsa", "hisse", "temettü", "kripto", "bitcoin", "ihale", "şirket", "yatırım", "finans", "ekonomi", "merkez bankası", "tcmb"],
        "Spor": ["gol", "maç", "skor", "futbol", "basketbol", "fenerbahçe", "galatasaray", "beşiktaş", "transfer", "kulüp", "başkan", "saran", "ali koç", "şampiyon", "lig", "antrenman", "sadettin saran", "volkan demirel", "mourinho", "fatih terim"],
        "Teknoloji": ["iphone", "apple", "android", "yazılım", "yapay zeka", "ai", "internet", "google", "çip", "uzay", "robot", "teknoloji", "aplikasyon", "nvidia", "openai"],
        "Eğlence": ["film", "dizi", "netflix", "sinema", "oyuncu", "magazin", "ünlü", "televizyon", "oscar", "altın portakal"],
        "Müzik": ["şarkı", "albüm", "konser", "klip", "single", "sanatçı", "spotify", "müzik", "eurovision", "grammy"],
        "Dünya": ["savaş", "abd", "rusya", "israil", "gazze", "nato", "avrupa", "bm", "pentagon", "beyaz saray"],
        "Türkiye": ["siyaset", "seçim", "meclis", "parti", "istifa", "belediye", "trt", "aa", "ankara", "ak parti", "chp", "mhp", "iyi parti", "dem parti", "erdoğan", "özel", "imamoğlu", "yavaş"]
    }
    
    for cat, words in keywords.items():
        if any(word in text for word in words):
            return cat
    return "Türkiye" # Varsayılan kategori

def categorize_tweet(tweet_text, username=None):
    """
    Kategori belirleme (STRICT MAPPING V45.0):
    1. Önce veritabanındaki kayıtlı kategorisine (sources tablosu) bakar.
    2. Kayıtlı değilse anahtar kelimelere göre belirler ve veritabanına kaydeder.
    """
    from database import get_source_category
    
    if username:
        # Temiz kullanıcı adı
        clean_user = username.lower().replace("@", "").strip()
        db_cat = get_source_category(clean_user)
        if db_cat:
            return db_cat

    # Kayıtlı değilse veya username yoksa fallback yap
    return get_fallback_category(tweet_text, username=username)

def get_full_analysis(tweet_text, username=None):
    """Kategori ve Konu Etiketini beraber döner (AI Off)."""
    cat = categorize_tweet(tweet_text, username=username)
    tag = generate_topic_tag(tweet_text)
    return cat, tag

def process_single_account(username):
    """Tek bir hesap için verileri çeker ve ön işleme yapar."""
    try:
        tweets = fetch_user_tweets(username, limit=15)
        return username, tweets
    except Exception:
        return username, []

def run_categorization_process():
    """Tüm hedef hesaplardan tweetleri PARALEL (Multithreaded) çeker ve kaydeder."""
    target_accounts = list(SOURCE_MAPPING.keys())
    
    print("-" * 50)
    print("🚀 NucleusX ULTRA FAST Haber Sınıflandırıcı Başlıyor...")
    print("-" * 50)
    
    yield "⚡ Haber kaynakları paralel olarak taranıyor (Işık hızı)..."
    
    all_new_tweets = []
    
    # 1. Aşama: Tweetleri PARALEL olarak çek
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = {executor.submit(process_single_account, user): user for user in target_accounts}
        
        for future in as_completed(future_to_user):
            username, tweets = future.result()
            if tweets:
                all_new_tweets.extend(tweets)
                yield f"📡 {username} çekildi ({len(tweets)} haber)"

    # 2. Aşama: Veritabanına kaydet (Seri ama hızlı DB checkleri ile)
    yield "💾 Haberler veritabanına işleniyor..."
    
    count = 0
    for tweet in all_new_tweets:
        # Hızlı mükerrer kontrolü
        if not tweet_exists(tweet['username'], tweet['text']):
            kategori, konu_etiketi = get_full_analysis(tweet['text'], username=tweet['username'])
            save_tweet(
                tweet['author'], 
                tweet['username'], 
                tweet['text'], 
                kategori, 
                konu_etiketi, 
                media_url=tweet.get('media_url'), 
                tweet_url=tweet.get('tweet_url'),
                author_image=tweet.get('author_image'),
                has_video=tweet.get('has_video', False),
                reply_count=tweet.get('reply_count', 0),
                retweet_count=tweet.get('retweet_count', 0),
                like_count=tweet.get('like_count', 0)
            )
            count += 1
            if count % 10 == 0:
                yield f"✅ {count} yeni haber eklendi..."
    
    yield f"🏁 Bitti! Toplam {count} benzersiz haber sisteme kazandırıldı."
    print(f"\n✅ Analiz Tamamlandı! {count} haber işlendi.")

if __name__ == "__main__":
    init_db()
    populate_sources_table() # Kaynakları senkronize et
    for status in run_categorization_process():
        print(status)
