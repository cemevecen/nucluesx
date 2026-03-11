# NucleusX AI - Production Build: v7.0 (Clean & Optimized)
import streamlit as st
import re
import pandas as pd
import sqlite3
from database import DB_NAME, init_db
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
        background-color: #0e1117;
        padding: 0;
    }
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important;
    }
    /* Scoopnest Style Column Header */
    .column-header {
        padding: 10px;
        border-bottom: 3px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        text-align: center;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px 10px 0 0;
    }
    .news-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
    }
    .news-card:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .author-info {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .author-name {
        color: #60a5fa;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .tweet-content {
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.4;
        margin-bottom: 12px;
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: #94a3b8;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        padding-top: 10px;
    }
    .interaction-icons {
        display: flex;
        gap: 15px;
        color: #60a5fa;
    }
    
    /* YATAY SCROLL (KAYDIRMA) ÖZELLİĞİ */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        overflow-x: scroll !important; /* Her zaman scroll edilebilir */
        flex-wrap: nowrap !important;
        gap: 15px !important;
        padding-bottom: 25px !important;
        scrollbar-width: thin;
        scrollbar-color: #60a5fa rgba(255,255,255,0.1);
    }
    
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar {
        height: 10px; /* Daha belirgin scrollbar */
    }
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar-thumb {
        background: #60a5fa;
        border-radius: 5px;
    }
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    div[data-testid="column"] {
        /* Ekranda tam 5 tane sığması için %19.2 (boşluklar dahil) */
        min-width: calc(19.2% - 12px) !important; 
        flex: 0 0 auto !important;
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
        conn = sqlite3.connect(DB_NAME)
        # media_url sütununu da çekiyoruz
        query = "SELECT * FROM tweets ORDER BY processed_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        # Tablo henüz oluşmamış veya başka bir hata varsa boş DF döndür
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
                
                st.markdown(f"""
                    <div class="news-card">
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
                    </div>
                """, unsafe_allow_html=True)

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
