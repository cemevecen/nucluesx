import streamlit as st
import re
import pandas as pd
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

# Premium CSS - Mockup Matching Design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }

    /* Ana Arka Plan */
    .stApp {
        background-color: #f8fafc !important;
    }
    
    /* Header (Top Nav) */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 40px;
        background: white;
        border-bottom: 1px solid #e2e8f0;
        position: sticky;
        top: 0;
        z-index: 1000;
        margin-bottom: 25px;
        margin-left: -5rem;
        margin-right: -5rem;
    }
    .logo-text {
        font-weight: 800;
        font-size: 1.5rem;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .search-box {
        background: #f1f5f9;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        width: 400px;
        color: #64748b;
        font-size: 0.9rem;
    }

    /* Sidebar - DARK SLATE */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        color: white !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    .sidebar-item {
        padding: 12px 20px;
        display: flex;
        align-items: center;
        gap: 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        transition: all 0.2s;
        cursor: pointer;
        font-size: 0.9rem;
        color: #94a3b8 !important;
    }
    .sidebar-item:hover, .sidebar-item.active {
        background: rgba(255,255,255,0.1);
        color: white !important;
    }

    /* Trending Topics Bar */
    .trending-title {
        font-weight: 700;
        font-size: 1.2rem;
        color: #1e293b;
        margin-bottom: 15px;
    }
    .trend-pill {
        border: 1px solid #cbd5e1 !important;
        border-radius: 30px !important;
        padding: 8px 20px !important;
        background: white !important;
        color: #1e40af !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s;
        text-align: center;
    }

    /* News Cards */
    .news-card {
        background: #ffffff !important;
        border-radius: 16px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    .card-title {
        color: #1e40af !important;
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.3;
        margin-bottom: 8px;
    }
    .card-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 12px;
    }

    /* Column Headers */
    .column-header {
        height: 70px;
        background: white;
        border-radius: 12px;
        display: flex;
        align-items: center;
        padding: 0 20px;
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
        color: #1e293b;
        font-weight: 700;
    }

    /* Layout Reset */
    .block-container {
        padding-top: 0rem !important;
        padding-left: 5rem !important;
        padding-right: 5rem !important;
    }
    
    /* Horizontal Swipe */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        overflow-x: auto !important;
        gap: 20px !important;
        padding-bottom: 30px !important;
        scrollbar-width: none;
    }
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar { display: none; }
    
    div[data-testid="column"] {
        flex: 0 0 calc(19% - 16px) !important;
        min-width: 300px !important;
        flex-shrink: 0 !important;
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

# Veritabanı verisini önbelleğe alalım (Hız İçin Kritik!)
# ttl=300 (5 dakika) boyunca aynı veriyi sunar, sonra yeniler.
@st.cache_data(ttl=300)
def load_data():
    try:
        conn = get_db_connection()
        # Sadece son 3 gündeki haberleri çekelim ki tablo şişmesin (Hız kazandırır)
        query = "SELECT author, username, content, category, topic_tag, processed_at, media_url FROM tweets WHERE processed_at > NOW() - INTERVAL '3 days' ORDER BY processed_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if not df.empty:
            df['processed_at'] = df['processed_at'].astype(str)
        return df
    except Exception as e:
        st.error(f"Veri yüklenirken hata oluştu: {e}")
        return pd.DataFrame(columns=['author', 'username', 'content', 'category', 'topic_tag', 'processed_at', 'media_url'])

# Kenar Çubuğu
st.sidebar.title("🚀 NucleusX AI")
st.sidebar.markdown("---")

# Sabit Değişkenler
GENERIC_TAG_LIST = ["#GELISME", "#GELİŞME", "#GUNDEM", "#GÜNDEM", "#HABER", "#DETAY", "#SONDAKIKA", "#SONDAKİKA"]

# Güvenlik ve Kotayı Korumak İçin: Admin Girişi
with st.sidebar.expander("🔐 Yönetici Paneli"):
    admin_password = st.text_input("Tarama Şifresi", type="password")
    ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "nucleus123")

st.sidebar.markdown("---")

# Veriyi Yükle
df = load_data()

# Kenar Çubuğu Filtreleme
categories = ["Tümü"] + list(df['category'].unique()) if not df.empty else ["Tümü"]
selected_cat = st.sidebar.selectbox("Kategori Filtrele", categories)

if selected_cat != "Tümü" and not df.empty:
    df = df[df['category'] == selected_cat]

# Oturum Durumu (Hashtag Filtresi İçin)
if 'selected_tag' not in st.session_state:
    st.session_state.selected_tag = None

def clear_tag():
    st.session_state.selected_tag = None

# CSS Override for stButton to match trend-pill
st.markdown("""
    <style>
    div.stButton > button:first-child[key^="t_"] {
        border: 1px solid #cbd5e1 !important;
        border-radius: 30px !important;
        background: white !important;
        color: #1e40af !important;
        height: 40px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sticky Top Nav (Logo & Search)
st.markdown("""
    <div class="top-nav">
        <div class="logo-text">
            <span>⚛️</span> NUCLEUS<b>X</b> <span style="font-size: 0.8rem; opacity: 0.6; font-weight: 400;">AI NEWSROOM</span>
        </div>
        <div class="search-box">🔍 Search news, events or topics...</div>
        <div style="display: flex; gap: 20px; align-items: center; font-size: 1.2rem;">
            <span>❓</span> <span>🔔</span> <span style="background: #e2e8f0; width: 35px; height: 35px; border-radius: 50%; padding: 5px; cursor: pointer;">👤</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Custom Sidebar content
with st.sidebar:
    st.markdown("""
        <div style="margin-top: 20px;">
            <div class="sidebar-item active">📊 Dashboard</div>
            <div class="sidebar-item">🧭 Explore</div>
            <div class="sidebar-item">⚖️ Politics</div>
            <div class="sidebar-item">💼 Business</div>
            <div class="sidebar-item">💻 Tech</div>
            <div class="sidebar-item">🌍 World</div>
            <div class="sidebar-item">🔬 Science</div>
            <div class="sidebar-item">💰 Finance</div>
        </div>
    """, unsafe_allow_html=True)
    st.info("Bu panel, Twitter'dan çekilen ve AI tarafından kategorize edilen haberleri gösterir.")

# TREND HASHTAGLER
if not df.empty:
    popular_tags = df[~df['topic_tag'].isin(GENERIC_TAG_LIST)]['topic_tag'].value_counts().head(8).index.tolist()
    if popular_tags:
        st.markdown('<div class="trending-title">Trending Topics</div>', unsafe_allow_html=True)
        tag_cols = st.columns(len(popular_tags) + 1)
        for idx, tag in enumerate(popular_tags):
            if tag_cols[idx].button(tag, key=f"t_{tag}", use_container_width=True):
                st.session_state.selected_tag = tag
                st.rerun()
        if st.session_state.selected_tag:
            tag_cols[-1].button("❌ Reset", on_click=clear_tag)

st.markdown("<br>", unsafe_allow_html=True)

# FİLTRELİ KONU GÖRÜNÜMÜ
if st.session_state.selected_tag:
    st.markdown(f"### 📍 {st.session_state.selected_tag} Hakkındaki Tüm Gelişmeler")
    tag_df = df[df['topic_tag'] == st.session_state.selected_tag]
    
    tag_cols = st.columns(3)
    for idx, row in tag_df.iterrows():
        with tag_cols[idx % 3]:
            clickable_content = make_clickable(row['content'])
            media_html = f'<img src="{row["media_url"]}" style="width:100%; border-radius:12px; margin-bottom:12px; object-fit:cover; height:220px; background:#f1f5f9;">' if row.get('media_url') else ""
            st.markdown(f"""
                <div class="news-card">
                    {media_html}
                    <div class="tweet-content"><b>{row['author']}</b>: {clickable_content}</div>
                    <div class="card-footer">
                        <span>🕒 {row['processed_at'].split(' ')[1][:5]}</span>
                        <span style="color:#2563eb;">{row['category']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    if st.button("⬅️ Ana Sayfaya Dön", on_click=clear_tag):
        st.rerun()
    st.stop()

# NORMAL GÖRÜNÜM (Scoopnest Dikey Kolon Düzeni)

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
        
        cat_df = df[df['category'] == category].head(30)
        
        if cat_df.empty:
            st.info(f"Henüz {category} haberi yok.")
        else:
            # Tüm kolon içeriğini tek bir HTML bloğunda toplayalım (Kayma ve bozulmayı önler)
            column_html = ""
            cat_df['topic_tag'] = cat_df['topic_tag'].str.strip().str.upper()
            topics = cat_df.groupby('topic_tag')
            
            GENERIC_TAGS = ["#GELISME", "#GELİŞME", "#GUNDEM", "#GÜNDEM", "#HABER", "#DETAY", "#SONDAKIKA", "#SONDAKİKA"]

            for tag, group in topics:
                group = group.sort_values('processed_at', ascending=False).drop_duplicates(subset=['author']) 
                main_news = group.iloc[0]
                # Başlık ve içerik ayrımı (Eğer ":" varsa öncesi başlık gibi düşünülür mockup'ta)
                title_part = main_news['content'].split(':')[0] if ':' in main_news['content'] else main_news['author']
                desc_part = main_news['content'].split(':')[1] if ':' in main_news['content'] else main_news['content']
                
                media_html = f'<img src="{main_news["media_url"]}" style="width:100%; border-radius:12px; margin-bottom:12px; object-fit:cover; height:180px; background:#f1f5f9;">' if main_news.get('media_url') else ""
                
                count_info = f'<div style="color:#2563eb; font-weight:bold; margin-top:8px;">✨ {len(group)} farklı kaynak bu olayı geçti.</div>' if len(group) > 1 else ""
                
                column_html += f"""
                    <div class="news-card">
                        {media_html}
                        <div class="card-title">{title_part}</div>
                        <div style="font-size:0.9rem; color:#475569; margin-top:5px;">{desc_part[:150]}...</div>
                        <div class="card-meta">
                            <span>🔹 {main_news['author']}</span>
                            <span>🕒 {main_news['processed_at'].split(' ')[1][:5]}</span>
                            <span>📖 5 Dakika Okuma</span>
                            <span style="color:#2563eb;">{tag}</span>
                        </div>
                        {count_info}
                    </div>
                """
            st.markdown(column_html, unsafe_allow_html=True)

# Manuel Yenileme Butonu (Test İçin Sınırsız, Ancak Kota Dostu)
if st.sidebar.button("🔄 Şimdi Yeni Haberleri Tara"):
    # 1. Şifre Kontrolü
    if admin_password != ADMIN_PASS:
        st.sidebar.error("❌ Hatalı şifre! Tarama izniniz yok.")
    else:
        # Motor artık adım adım (generator) çalıştığı için döngüyle bildirim alıyoruz
        status_text = st.sidebar.empty()
        with st.spinner("🚀 NucleusX AI Haberleri Topluyor..."):
            try:
                for update in run_categorization_process():
                    status_text.info(update)
                st.success("✅ Tarama tamamlandı! Sayfa yenileniyor...")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Tarama sırasında bir hata oluştu: {e}")

def recategorize_all_news():
    """Veritabanındaki TÜM haberleri AI ile tekrar tarayıp hashtag (#) atar. 
    Özellikle #GUNDEM ve #GELISME etiketlerini temizler ve mükerrerleri gruplar."""
    from database import get_db_connection
    from categorize_engine import get_full_analysis
    conn = get_db_connection()
    cursor = conn.cursor()
    # Tüm haberleri tarayalım (Özellikle eski etiketleri temizlemek için)
    cursor.execute("SELECT id, content FROM tweets")
    rows = cursor.fetchall()
    
    yield f"🧹 {len(rows)} haber için derin analiz başlıyor..."
    
    for row_id, content in rows:
        cat, tag = get_full_analysis(content)
        cursor.execute("UPDATE tweets SET category = %s, topic_tag = %s WHERE id = %s", (cat, tag, row_id))
        conn.commit()
        yield f"♻️ {tag} [{cat}] (ID: {row_id})"
    
    conn.close()
    yield "✅ Veritabanı başarıyla optimize edildi!"

# MİGRASYON / BAKIM BUTONU
if st.sidebar.button("🧹 Tüm Veritabanını Optimize Et"):
    if admin_password != ADMIN_PASS:
        st.sidebar.error("❌ Yönetici yetkisi gerekli.")
    else:
        status_text = st.sidebar.empty()
        with st.spinner("🛠️ Eski haberler kümeleniyor..."):
            try:
                for log in recategorize_all_news():
                    status_text.info(log)
                # Önbelleği temizleyelim ki yeni hashtagler hemen gelsin
                st.cache_data.clear()
                st.success("✨ Tüm geçmiş veriler optimize edildi!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Optimizasyon hatası: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("🚀 **NucleusX Engine v7.0**")
st.sidebar.caption("Developed by Antigravity AI 🤖")
