import streamlit as st
import pandas as pd
import sqlite3
from database import DB_NAME, init_db
import time

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="NucleusX AI | Haber Havuzu",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Canlı yayında veritabanı yoksa oluştur
init_db()

# Premium CSS - Glassmorphism ve Modern Tasarım
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
    }
    .news-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .news-card:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .category-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    .cat-ekonomi { background: #1e3a8a; color: #bfdbfe; }
    .cat-spor { background: #064e3b; color: #d1fae5; }
    .cat-teknoloji { background: #581c87; color: #f3e8ff; }
    .cat-eglence { background: #831843; color: #fce7f3; }
    .cat-diger { background: #374151; color: #f3f4f6; }
    
    .author-name {
        color: #60a5fa;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .tweet-content {
        color: #e2e8f0;
        font-size: 1.1rem;
        line-height: 1.5;
    }
    .time-stamp {
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        conn = sqlite3.connect(DB_NAME)
        query = "SELECT * FROM tweets ORDER BY processed_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        # Tablo henüz oluşmamış veya başka bir hata varsa boş DF döndür
        return pd.DataFrame(columns=['author', 'username', 'content', 'category', 'processed_at'])

# Kenar Çubuğu
st.sidebar.title("🚀 NucleusX AI")
st.sidebar.markdown("---")
st.sidebar.info("Bu panel, Twitter'dan çekilen ve AI tarafından kategorize edilen haberleri gösterir.")

# Filtreleme
df = load_data()
categories = ["Tümü"] + list(df['category'].unique())
selected_cat = st.sidebar.selectbox("Kategori Filtrele", categories)

if selected_cat != "Tümü":
    df = df[df['category'] == selected_cat]

# Ana Ekran
st.title("🗞️ Canlı Haber Akışı")
st.markdown(f"**Toplam {len(df)} haber listeleniyor.**")

# İstatistikler - Küçük Widgetlar
c1, c2, c3, c4 = st.columns(4)
stats = df['category'].value_counts()

with c1:
    st.metric("Ekonomi", stats.get("Ekonomi", 0))
with c2:
    st.metric("Spor", stats.get("Spor", 0))
with c3:
    st.metric("Teknoloji", stats.get("Teknoloji", 0))
with c4:
    st.metric("Eğlence", stats.get("Eğlence", 0))

st.markdown("---")

# Haber Listesi
if df.empty:
    st.warning("Henüz veritabanında haber yok. Lütfen tarayıcıyı çalıştırın.")
else:
    for index, row in df.iterrows():
        cat_class = f"cat-{row['category'].lower().replace('ç', 'c').replace('ö', 'o').replace('ü', 'u').replace('ğ', 'g').replace('ı', 'i')}"
        
        st.markdown(f"""
            <div class="news-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="author-name">{row['author']} ({row['username']})</span>
                    <span class="category-badge {cat_class}">{row['category']}</span>
                </div>
                <div class="tweet-content">
                    {row['content']}
                </div>
                <div class="time-stamp">
                    🕒 {row['processed_at']}
                </div>
            </div>
        """, unsafe_allow_html=True)

# Manuel Yenileme Butonu
if st.sidebar.button("🔄 Şimdi Yeni Haberleri Tara"):
    with st.spinner("AI Haberleri Topluyor..."):
        import subprocess
        subprocess.run(["python3", "categorize_engine.py"])
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("Developed by Antigravity AI 🤖")
