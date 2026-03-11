# NucleusX AI - Production Build: v7.0 (Clean & Optimized)
import streamlit as st
import re
import pandas as pd
import sqlite3
from database import init_db, get_db_connection
import time
from categorize_engine import run_categorization_process

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
        background-color: #ffffff;
        padding: 0;
    }
    .stApp {
        background-color: #f8fafc;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important;
    }
    /* Light Mode Column Header */
    .column-header {
        padding: 10px;
        border-bottom: 3px solid #2563eb;
        margin-bottom: 20px;
        text-align: center;
        background: #ffffff;
        border-radius: 10px 10px 0 0;
        color: #1e293b;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .news-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .news-card:hover {
        transform: translateY(-5px);
        border: 1px solid #2563eb;
        background: #ffffff;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .author-info {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .author-name {
        color: #2563eb;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .tweet-content {
        color: #0f172a;
        font-size: 0.95rem;
        line-height: 1.4;
        margin-bottom: 12px;
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: #64748b;
        border-top: 1px solid #f1f5f9;
        padding-top: 10px;
    }
    
    /* YATAY SCROLL (LIGHT THEME) */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        overflow-x: scroll !important;
        flex-wrap: nowrap !important;
        gap: 15px !important;
        padding-bottom: 25px !important;
        scrollbar-width: thin;
        scrollbar-color: #2563eb #f1f5f9;
    }
    
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar {
        height: 8px;
    }
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar-thumb {
        background: #2563eb;
        border-radius: 10px;
    }
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    
    div[data-testid="column"] {
        min-width: calc(19.2% - 12px) !important; 
        flex: 0 0 auto !important;
    }

    h1, h2, h3, p {
        color: #0f172a !important;
    }
    </style>
""", unsafe_allow_html=True)

def make_clickable(text):
    """Metindeki linkleri ve @kullanıcı adlarını tıklanabilir HTML yapar."""
    # Linkleri bul ve çevir
    text = re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" style="color: #60a5fa; text-decoration: none;">\1</a>', text)
    # @kullanıcı adlarını bul ve X.com linkine çevir
    text = re.sub(r'@(\w+)', r'<a href="https://x.com/\1" target="_blank" style="color: #60a5fa; text-decoration: none;">@\1</a>', text)
    return text

def load_data():
    try:
        conn = get_db_connection()
        query = "SELECT author, username, content, category, processed_at, media_url FROM tweets ORDER BY processed_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        # Tarih formatını pandas üzerinden düzeltelim (PostgreSQL'den gelen tipi koruyarak)
        if not df.empty:
            df['processed_at'] = df['processed_at'].astype(str)
        return df
    except Exception as e:
        st.error(f"Veri yüklenirken hata oluştu: {e}")
        return pd.DataFrame(columns=['author', 'username', 'content', 'category', 'processed_at', 'media_url'])

# Kenar Çubuğu
st.sidebar.title("🚀 NucleusX AI")
st.sidebar.markdown("---")

# Güvenlik ve Kotayı Korumak İçin: Admin Girişi (Basit Bir Önlem)
# Bu kısım botların veya rastgele kullanıcıların 'Scan' butonuna basıp kotanızı bitirmesini engeller.
with st.sidebar.expander("🔐 Yönetici Paneli"):
    admin_password = st.text_input("Tarama Şifresi", type="password")
    # Örnek şifre 'nucleus123' - Bunu Streamlit Secrets üzerinden yönetmek daha güvenlidir.
    ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "nucleus123")

st.sidebar.markdown("---")
st.sidebar.info("Bu panel, Twitter'dan çekilen ve AI tarafından kategorize edilen haberleri gösterir.")

# Filtreleme
df = load_data()
categories = ["Tümü"] + list(df['category'].unique())
selected_cat = st.sidebar.selectbox("Kategori Filtrele", categories)

if selected_cat != "Tümü":
    df = df[df['category'] == selected_cat]

# Ana Ekran - Scoopnest Dikey Kolon Düzeni
st.title("🎙️ NucleusX AI Newsroom")
st.markdown("---")

# Veriyi Kategorilere Göre Hazırla
# Tüm 8 kategoriyi tek bir satırda (side-by-side) döküyoruz
all_categories = ["Ülke Gündemi", "Dünya", "Ekonomi", "Finans", "Teknoloji", "Spor", "Eğlence", "Müzik"]

cols = st.columns(len(all_categories))

for i, category in enumerate(all_categories):
    with cols[i]:
        # Kolon Başlığı
        st.markdown(f"""
            <div class="column-header">
                <h3 style="font-size: 1rem;">{category}</h3>
                <small>{len(df[df['category'] == category])} Haber</small>
            </div>
        """, unsafe_allow_html=True)
        
        cat_df = df[df['category'] == category].head(10)
        
        if cat_df.empty:
            st.info(f"Henüz {category} haberi yok.")
        else:
            for index, row in cat_df.iterrows():
                # Tıklanabilir içerik
                clickable_content = make_clickable(row['content'])
                username_link = f"https://x.com/{row['username'].replace('@', '')}"
                
                # Resim varsa HTML hazırla
                media_html = f'<img src="{row["media_url"]}" style="width:100%; border-radius:10px; margin-bottom:10px;">' if row.get('media_url') else ""
                
                st.markdown(f"""<div class="news-card">
<div class="author-info">
<a href="{username_link}" target="_blank" style="text-decoration: none;">
<span class="author-name" style="font-size: 0.8rem;">{row['author']}</span>
<span style="color: #4b5563; font-size: 0.7rem;">{row['username']}</span>
</a>
</div>
{media_html}
<div class="tweet-content" style="font-size: 0.85rem;">
{clickable_content}
</div>
<div class="card-footer" style="padding-top: 5px;">
<div class="time-stamp">
{row['processed_at'].split(' ')[1][:5]}
</div>
</div>
</div>""", unsafe_allow_html=True)

# Manuel Yenileme Butonu (Test İçin Sınırsız, Ancak Kota Dostu)
if st.sidebar.button("🔄 Şimdi Yeni Haberleri Tara"):
    # 1. Şifre Kontrolü
    if admin_password != ADMIN_PASS:
        st.sidebar.error("❌ Hatalı şifre! Tarama izniniz yok.")
    else:
        # Not: Mükerrer kontrolü (database.py) ve API geciktirici (categorize_engine.py) 
        # sayesinde sınırsız tıklanabilir, fatura oluşturmaz.
        # Gerçek zamanlı ilerleme mesajları için boş bir yer tutucu
        status_text = st.sidebar.empty()
        with st.spinner("🚀 NucleusX AI Haberleri Topluyor..."):
            try:
                # Motor artık adım adım (generator) çalıştığı için döngüyle bildirim alıyoruz
                for update in run_categorization_process():
                    status_text.info(update)
                
                st.success("✅ Tarama tamamlandı! Sayfa yenileniyor...")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Tarama sırasında bir hata oluştu: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("🚀 **NucleusX Engine v7.0**")
st.sidebar.caption("Developed by Antigravity AI 🤖")
