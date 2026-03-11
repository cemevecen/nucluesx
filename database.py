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
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

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
                media_url TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Mükerrer kaydı önlemek için UNIQUE index (PostgreSQL stili)
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS unique_tweet_idx ON tweets (username, md5(content));
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"✅ Supabase Bağlantı Hatası: {e}")

def save_tweet(author, username, content, category, media_url=None):
    """Tweet verisini Supabase'e kaydeder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tweets (author, username, content, category, media_url) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (author, username, content, category, media_url)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ Veritabanına kaydederken hata oluştu: {e}")
    finally:
        cursor.close()
        conn.close()

def tweet_exists(username, content):
    """Tweetin zaten kaydedilip edilmediğini kontrol eder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # PostgreSQL'de içerik çok uzunsa md5 ile kontrol edebiliriz
    cursor.execute(
        "SELECT id FROM tweets WHERE username = %s AND content = %s LIMIT 1",
        (username, content)
    )
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists
