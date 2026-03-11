# NucleusX AI - Deployment Refresh: v1.1
import streamlit as st
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
# 8 kategoriyi 2 satıra (4+4) bölerek gösteriyoruz ki kolonlar çok daralmasın
categories_row1 = ["Ülke Gündemi", "Dünya", "Ekonomi", "Finans"]
categories_row2 = ["Teknoloji", "Spor", "Eğlence", "Müzik"]

def render_category_columns(cat_list):
    cols = st.columns(len(cat_list))
    for i, category in enumerate(cat_list):
        with cols[i]:
            # Kolon Başlığı
            st.markdown(f"""
                <div class="column-header">
                    <h3>{category}</h3>
                    <small>{len(df[df['category'] == category])} Haber</small>
                </div>
            """, unsafe_allow_html=True)
            
            cat_df = df[df['category'] == category].head(10)
            
            if cat_df.empty:
                st.info(f"Henüz {category} haberi yok.")
            else:
                for index, row in cat_df.iterrows():
                    st.markdown(f"""
                        <div class="news-card">
                            <div class="author-info">
                                <span class="author-name">{row['author']}</span>
                                <span style="color: #4b5563; font-size: 0.7rem;">{row['username']}</span>
                            </div>
                            <div class="tweet-content">
                                {row['content']}
                            </div>
                            <div class="card-footer">
                                <div class="interaction-icons">
                                    <span>💬</span> <span>🔄</span> <span>❤️</span>
                                </div>
                                <div class="time-stamp">
                                    {row['processed_at'].split(' ')[1][:5]}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

# İlk Satır
render_category_columns(categories_row1)
st.markdown("<br>", unsafe_allow_html=True)
# İkinci Satır
render_category_columns(categories_row2)

# Manuel Yenileme Butonu (Test İçin Sınırsız, Ancak Kota Dostu)
if st.sidebar.button("🔄 Şimdi Yeni Haberleri Tara"):
    # 1. Şifre Kontrolü
    if admin_password != ADMIN_PASS:
        st.sidebar.error("❌ Hatalı şifre! Tarama izniniz yok.")
    else:
        # Not: Mükerrer kontrolü (database.py) ve API geciktirici (categorize_engine.py) 
        # sayesinde sınırsız tıklanabilir, fatura oluşturmaz.
        with st.spinner("🚀 NucleusX AI Haberleri Topluyor..."):
            try:
                run_categorization_process()
                st.success("✅ Tarama tamamlandı! Mükerrer haberler otomatik atlandı.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Tarama sırasında bir hata oluştu: {e}")

st.sidebar.markdown("---")
st.sidebar.write("Developed by Antigravity AI 🤖")
