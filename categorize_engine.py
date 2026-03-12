import os
from google import genai
from dotenv import load_dotenv
from database import init_db, save_tweet, tweet_exists
import time
import requests
from twitter_scraper import fetch_user_tweets

# .env dosyasındaki anahtarları yükler
load_dotenv()

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
    Haber metni için BENZERSİZ ve OLAY ODAKLI bir hashtag (#) üretir.
    Amacı: Farklı kaynaklar aynı olaydan bahsettiğinde aynı etiketi almalarını sağlamaktır.
    """
    if client_gemini:
        try:
            prompt = f"""
            Aşağıdaki haber metninden SADECE ana özneyi ve olayı içeren bir hashtag üret.
            KURALLAR:
            1. Genel etiketler (#HABER, #GUNDEM, #SONDAKIKA) KESİNLİKLE YASAKTIR.
            2. Haberin ana kişisini VE ana konusunu birleştirerek tek bir etiket yap. (Örn: #FENERBAHCE_DIARRA, #BESIKTAS_TRANSFER, #ASGARI_UCRET_ZAMMI)
            3. Eğer haber bir kişi hakkındaysa SADECE o kişinin adını kullanabilirsin. (Örn: #RECEP_TAYYIP_ERDOGAN)
            4. SADECE etiketi dön, başka hiçbir şey yazma.
            5. Boşluk kullanma, kelimeleri alt tire (_) ile ayır.
            
            Metin: {text}
            """
            response = client_gemini.models.generate_content(model='gemini-flash-latest', contents=prompt)
            res = response.text.upper().strip().split()[0].replace(".", "").replace(",", "").replace('"', '').replace("'", "")
            if not res.startswith("#"): res = f"#{res}"
            
            if len(res) < 3 or res in ["#GUNDEM", "#GELISME", "#HABER"]:
                return "#DETAY"
            return res
        except: pass
    return "#HABER"

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

def get_fallback_category(text):
    """AI hata verdiğinde anahtar kelimelerle kategori tahmini yapar."""
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

def categorize_tweet(tweet_text):
    """
    Kategori belirleme zinciri: 
    1. Gemini (Ana) -> 2. Groq (Llama-3) -> 3. Mistral -> 4. Anahtar Kelime
    """
    
    # 1. Aşama: Gemini Dene
    if client_gemini:
        try:
            prompt = f"""Aşağıdaki haberi bu kategorilerden birine yerleştir: Ekonomi, Spor, Teknoloji, Eğlence, Müzik, Dünya, Türkiye.

KATEGORİ REHBERİ:
- Spor: Maçlar, futbolcular, kulüp başkanları (Sadettin Saran, Ali Koç vb.) ve transferler.
- Ekonomi: Para, borsa, banka, şirket yönetimi, fiyat artışları.
- Teknoloji: Dijital yenilikler, telefonlar, AI, bilim (İnsan transferleri teknoloji DEĞİLDİR).
- Türkiye: Genel iç siyaset ve sosyal olaylar.

SADECE kategorinin adını dön.

Metin: {tweet_text}"""
            response = client_gemini.models.generate_content(
                model='gemini-flash-latest', # Çalışan ve güncel alias
                contents=prompt
            )
            res = response.text.strip().replace("[", "").replace("]", "").replace(".", "")
            if res in ["Ekonomi", "Spor", "Teknoloji", "Eğlence", "Müzik", "Dünya", "Türkiye"]:
                return res
        except Exception as e:
            print(f"⚠️ Gemini Hatası (Yedeğe geçiliyor): {e}")
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

def get_full_analysis(tweet_text):
    """Kategori ve Konu Etiketini beraber döner."""
    cat = categorize_tweet(tweet_text)
    tag = generate_topic_tag(tweet_text)
    return cat, tag

def run_categorization_process():
    """Tüm hedef hesaplardan tweetleri çeker, kategorize eder ve kaydeder."""
    target_accounts = [
        # Türkiye
        "pusholder", "ajans_muhbir", "haskologlu", "darkwebhaber",
        # Dünya
        "bbcturkce", "euronews_tr", "dw_turkce", "voaturkce",
        # Ekonomi (Merged Finans)
        "ozgurdemirtas", "temelanaliz", "ekonomimcom", "Econofia",
        "borsagundem", "ParaAnaliz", "InvestingTR", "paramevzu",
        # Teknoloji
        "shiftdelete", "webteknoloji", "donanimhaber", "teknoseyir",
        # Spor
        "yagosabuncuoglu", "sporx", "ntvspor", "beINSPORTS_TR",
        # Eğlence
        "boxofficeturkey", "raninitv", "birsenaltuntas1", "tokyophoner",
        # Müzik
        "MuzikOnair", "PopBizde", "murekkephaber", "Kultur_Sanat"
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
            # 1. Ön Kategori ve Mükerrer Kontrolü (Zaten varsa AI'ya sormaya gerek yok)
            # Haberlerin çoğu 'Ülke Gündemi' veya 'Dünya' olduğu için 
            # önce hızlıca bir kategori tahmini yapıp veritabanına soruyoruz.
            dummy_category = get_fallback_category(tweet['text'])
            if tweet_exists(tweet['username'], tweet['text'], category=dummy_category):
                print(f"⏩ {tweet['username']} için bu haber (veya benzeri) zaten sistemde var, atlanıyor.")
                continue

            print(f"\n👤 GÖNDEREN: {tweet['author']} ({tweet['username']})")
            print(f"📝 TWEET: {tweet['text'][:100]}...") # Uzun tweetleri keserek basıyoruz
            
            # 2. Rate Limiting (KOTA KORUMASI: SADECE ÜCRETSİZ PLANLAR)
            # Gemini Free 15 RPM / Groq Free 30 RPM limitlerini aşmamak için 
            # 4 saniye bekleme (Saniyede 15 istekten azına denk gelir). 
            # Bu sayede 'Maliyet Sıfır, Kesintisizlik Tam' olur.
            time.sleep(4) 

            # Yapay Zeka Devreye Girer
            kategori, konu_etiketi = get_full_analysis(tweet['text'])

            # Veritabanına kaydet (Resim ve Tweet Linki varsa ekle)
            save_tweet(tweet['author'], tweet['username'], tweet['text'], kategori, konu_etiketi, media_url=tweet.get('media_url'), tweet_url=tweet.get('tweet_url'))
            yield f"✅ {tweet['username']}: [{konu_etiketi}]"
    
    print("\n" + "-" * 50)
    print("✅ Analiz Tamamlandı! Tüm veriler NucleusX veritabanına işlendi.")

if __name__ == "__main__":
    init_db()
    for status in run_categorization_process():
        print(status)
