import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Supabase Bağlantı Bilgileri
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    """Supabase (PostgreSQL) veritabanına bağlanır."""
    try:
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            sslmode='require',
            connect_timeout=10
        )
    except Exception as e:
        print(f"❌ KRİTİK BAĞLANTI HATASI: {e}")
        raise e

def init_db():
    """Tabloları Supabase üzerinde hazırlar (Yoksa oluşturur)."""
    if not DB_HOST or not DB_PASS:
        print("⚠️ Supabase bağlantı bilgileri eksik! Lütfen Secrets'a ekleyin.")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tweets tablosunu oluştur (PostgreSQL uyumlu)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tweets (
                id SERIAL PRIMARY KEY,
                author TEXT,
                username TEXT,
                content TEXT,
                category TEXT,
                topic_tag TEXT,
                media_url TEXT,
                tweet_url TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # OTOMATİK MİGRASYONLAR (Sütunlar yoksa ekle)
        migrations = [
            "ALTER TABLE tweets ADD COLUMN IF NOT EXISTS topic_tag TEXT DEFAULT '#HABER'",
            "ALTER TABLE tweets ADD COLUMN IF NOT EXISTS media_url TEXT",
            "ALTER TABLE tweets ADD COLUMN IF NOT EXISTS tweet_url TEXT",
            "UPDATE tweets SET category = 'Ekonomi' WHERE category = 'Finans'", # Finans kategorisini Ekonomi ile birleştir
            "UPDATE tweets SET category = 'Türkiye' WHERE category = 'Ülke Gündemi'", # Ülke Gündemi adını Türkiye yap
            "UPDATE tweets SET category = 'Spor' WHERE content ILIKE '%Sadettin Saran%' AND category = 'Teknoloji'" # Misclassified Saran tweets
        ]
        for m in migrations:
            try:
                cursor.execute(m)
            except:
                pass
        
        # Mükerrer kaydı önlemek için UNIQUE index (PostgreSQL stili)
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS unique_tweet_idx ON tweets (username, (md5(content)));
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"✅ Supabase Bağlantı Hatası: {e}")

def save_tweet(author, username, content, category, topic_tag="#Gundem", media_url=None, tweet_url=None):
    """Tweet verisini Supabase'e kaydeder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tweets (author, username, content, category, topic_tag, media_url, tweet_url) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (author, username, content, category, topic_tag, media_url, tweet_url)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ Veritabanına kaydederken hata oluştu: {e}")
    finally:
        cursor.close()
        conn.close()

def tweet_exists(username, content, category=None):
    """
    Kategoriden bağımsız (GLOBAL) mükerrer kontrolü yapar.
    Aynı haberin farklı bir kategoride veya hesapta olmasını engeller.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Birebir aynı tweet (Aynı hesap)
    cursor.execute(
        "SELECT id FROM tweets WHERE username = %s AND content = %s LIMIT 1",
        (username, content)
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return True
        
    # 2. GLOBAL Çapraz Hesap Kontrolü (Haber başka bir kategoride olsa bile engelle)
    # Metnin ilk 40 karakterini kullanarak son 24 saatteki haberlerle karşılaştırıyoruz
    clean_snippet = content[:100].strip()
    cursor.execute(
        "SELECT id FROM tweets WHERE content LIKE %s AND processed_at > NOW() - INTERVAL '24 hours' LIMIT 1",
        (f"%{clean_snippet[:40]}%",)
    )
    exists = cursor.fetchone() is not None
    
    cursor.close()
    conn.close()
    return exists
