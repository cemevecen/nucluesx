import streamlit as st
import re
import pandas as pd
from database import init_db, get_db_connection
import time
from categorize_engine import run_categorization_process

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="NucleusX AI V15.0 CLEAN",
    page_icon=None,
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
        background-color: #ffffff !important;
    }
    
    /* Header (Top Nav) */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 40px;
        background: #ffffff;
        border-bottom: 2px solid #000000;
        position: sticky;
        top: 0;
        z-index: 1000;
        margin-bottom: 25px;
        margin-left: -5rem;
        margin-right: -5rem;
    }
    .logo-text {
        font-weight: 900;
        font-size: 1.6rem;
        color: #000000;
        letter-spacing: -1px;
    }
    .search-box {
        background: #f8fafc;
        border: 1px solid #000000;
        padding: 8px 15px;
        border-radius: 4px;
        width: 350px;
        color: #000000;
        font-size: 0.85rem;
    }

    /* Sidebar - PURE WHITE CLEAN */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #000000 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #000000 !important;
    }
    
    /* Premium Sidebar Buttons - V15.0 Minimalist */
    div[data-testid="stSidebar"] div.stButton > button {
        background-color: #ffffff !important;
        border: 1px solid #000000 !important;
        color: #000000 !important;
        text-align: left !important;
        padding: 10px 20px !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        border-radius: 0px !important; /* Sharp corners for clean look */
        transition: none !important;
        margin-bottom: 5px !important;
        width: 100% !important;
    }
    div[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #e0e0e0 !important;
        border-width: 1px !important;
    }

    /* News Cards */
    .news-card {
        background: #ffffff !important;
        border-radius: 0px;
        padding: 20px;
        border: 1px solid #000000;
        margin-bottom: 20px;
        box-shadow: none !important;
    }
    .card-title {
        color: #000000 !important;
        font-weight: 800;
        font-size: 1.1rem;
        line-height: 1.4;
        margin-bottom: 10px;
    }
    .card-meta {
        color: #000000 !important;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Column Headers - Grid Style */
    .column-header {
        height: 80px;
        background: #ffffff;
        border-radius: 0px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
        border: 1px solid #000000;
        box-shadow: none;
    }
    .column-header h3 {
        color: #000000 !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        white-space: nowrap;
    }
    .column-header small {
        color: #000000;
        font-size: 0.75rem;
    }

    /* Layout - Horizontal Grid */
    .block-container {
        padding-top: 0rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 100% !important;
    }
    
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        overflow-x: auto !important;
        gap: 20px !important;
        padding-bottom: 40px !important;
        scrollbar-width: none;
    }
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar { display: none; }
    
    div[data-testid="column"] {
        flex: 0 0 320px !important;
        min-width: 320px !important;
        flex-shrink: 0 !important;
        scroll-snap-align: start;
    }
    </style>
""", unsafe_allow_html=True)

def make_clickable(text):
    """Metindeki linkleri ve @kullanıcı adlarını tıklanabilir HTML yapar."""
    # Linkleri bul ve çevir
    text = re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" style="color: #000000; text-decoration: none;">\1</a>', text)
    # @kullanıcı adlarını bul ve X.com linkine çevir
    text = re.sub(r'@(\w+)', r'<a href="https://x.com/\1" target="_blank" style="color: #000000; text-decoration: none;">@\1</a>', text)
    return text

# Veritabanı verisini önbelleğe alalım (Hız İçin Kritik!)
# ttl=600 (10 dakika) boyunca aynı veriyi sunar.
@st.cache_data(ttl=600)
def load_data():
    try:
        conn = get_db_connection()
        # Sadece son 48 saatteki haberleri çekelim (3 gün verisi yavaşlatabilir)
        # Hız için sadece gerekli sütunları çekiyoruz
        query = """
            SELECT author, content, category, topic_tag, processed_at, media_url, tweet_url 
            FROM tweets 
            WHERE processed_at > NOW() - INTERVAL '48 hours' 
            ORDER BY processed_at DESC 
            LIMIT 200
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['processed_at'] = pd.to_datetime(df['processed_at']).dt.strftime('%H:%M')
            df['topic_tag'] = df['topic_tag'].fillna('HABER').str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"Veri yüklenirken hata oluştu: {e}")
        return pd.DataFrame()

# Kenar Çubuğu
st.sidebar.markdown("### NUCLEUS X")
st.sidebar.markdown("---")

# Sabit Değişkenler
GENERIC_TAG_LIST = ["#GELISME", "#GELİŞME", "#GUNDEM", "#GÜNDEM", "#HABER", "#DETAY", "#SONDAKIKA", "#SONDAKİKA"]

# Güvenlik ve Kotayı Korumak İçin: Admin Girişi
with st.sidebar.expander("Yönetici Paneli"):
    admin_password = st.text_input("Tarama Şifresi", type="password")
    ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "nucleus123")

st.sidebar.markdown("---")

# Veriyi Yükle
df = load_data()

# LOG BİLGİSİ
print("--- CLEAN LIGHT V15.0 DEPLOY ---")

# Canlıda cache'i temizle
if 'init_v15' not in st.session_state:
    st.cache_data.clear()
    st.session_state.init_v15 = True

# Oturum Durumu (Navigasyon ve Filtreler İçin)
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

if 'selected_tag' not in st.session_state:
    st.session_state.selected_tag = None

def clear_tag():
    st.session_state.selected_tag = None

def set_page(page_name):
    st.session_state.current_page = page_name
    st.session_state.selected_tag = None # Sayfa değişince etiketi sıfırla

# CSS Override for stButton to match trend-pill
st.markdown("""
    <style>
    div.stButton > button:first-child[key^="t_"] {
        border: 1px solid #000000 !important;
        border-radius: 30px !important;
        background: #ffffff !important;
        color: #000000 !important;
        height: 40px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sticky Top Nav (Logo & Search)
st.markdown("""
        <div class="logo-text">
            NUCLEUS <b>X</b> <span style="font-size: 0.8rem; opacity: 0.5;">v15.0 CLEAN</span>
        </div>
        <div class="search-box"> Haberlerde veya konularda ara...</div>
        <div style="display: flex; gap: 20px; align-items: center; font-size: 1.2rem;">
            <span></span> <span></span> <span style="background: #e0e0e0; width: 35px; height: 35px; border-radius: 50%; padding: 5px; cursor: pointer;"></span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Custom Sidebar navigation (Premium Style)
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Active item highlight CSS
    active_btn_name = st.session_state.current_page
    st.markdown(f"""
        <style>
        /* Highlight the active button by its label text (hacky but works in some ST versions) or just use logic */
        /* Since keys are internal, we use a simpler approach: adding a indicator */
        </style>
    """, unsafe_allow_html=True)

    # Navigasyon Menüsü - Sade ve Emojisiz (V12.0)
    nav_items = [
        {"name": "Dashboard", "label": "Ana Sayfa"},
        {"name": "Türkiye", "label": "Siyaset"},
        {"name": "Ekonomi", "label": "Ekonomi"},
        {"name": "Teknoloji", "label": "Teknoloji"},
        {"name": "Spor", "label": "Spor"},
        {"name": "Dünya", "label": "Dünya"},
        {"name": "Eğlence", "label": "Magazin"},
        {"name": "Müzik", "label": "Müzik"}
    ]
    
    for item in nav_items:
        is_active = st.session_state.current_page == item["name"]
        
        # Temiz buton etiketi (Emojisiz)
        btn_label = item['label']
        if is_active:
            # Aktif sayfa için özel stil
            st.sidebar.markdown(f"""
                <style>
                div[data-testid="stSidebar"] div.stButton > button[key="nav_btn_{item['name']}"] {{
                    background-color: #000000 !important;
                    color: #ffffff !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        
        if st.sidebar.button(btn_label, key=f"nav_btn_{item['name']}", use_container_width=True):
            st.session_state.current_page = item["name"]
            st.session_state.selected_tag = None
            st.rerun()

    st.markdown("---")
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
            
            # Başlığa Tıklandığında Twite Gitme Özelliği
            title_html = f'<div class="card-title"><a href="{row["tweet_url"]}" target="_blank">{row["author"]}</a></div>' if row.get('tweet_url') else f'<div class="card-title">{row["author"]}</div>'
            
            card_html = f'<div class="news-card">{media_html}{title_html}<div style="font-size:0.95rem; line-height:1.4;">{clickable_content}</div><div class="card-meta"><span>🕒 {row["processed_at"]}</span><span style="color:#2563eb;">{row["category"]}</span></div></div>'
            st.markdown(card_html, unsafe_allow_html=True)
    
    if st.button("⬅️ Ana Sayfaya Dön", on_click=clear_tag):
        st.rerun()
    st.stop()

# ANA İÇERİK MANTİĞİ
if st.session_state.current_page != "Dashboard":
    # TEK KATEGORİ GÖRÜNÜMÜ - ÖZEL SAYFA
    cat_name = st.session_state.current_page
    # Başlığı bulalım
    cat_label = next((item["label"] for item in nav_items if item["name"] == cat_name), cat_name)
    
    st.markdown(f"""
        <div style="padding: 20px; background: white; border-bottom: 2px solid #3b82f6; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h2 style="margin: 0; color: #1e293b; font-size: 1.8rem;">📍 {cat_label}</h2>
            <p style="margin: 5px 0 0 0; color: #64748b; font-size: 0.9rem;">En son {cat_name} haberleri ve gelişmeleri.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Filtreleme
    cat_df = df[df['category'] == cat_name].head(60)
    
    if cat_df.empty:
        st.warning(f"Bu kategoriye ait henüz haber bulunamadı.")
    else:
        # 3 Kolonlu Grid
        grid_cols = st.columns(3)
        for idx, row in cat_df.iterrows():
            with grid_cols[idx % 3]:
                clickable_content = make_clickable(row['content'])
                media_html = f'<img src="{row["media_url"]}" style="width:100%; border-radius:12px; margin-bottom:12px; object-fit:cover; height:220px; background:#f1f5f9;">' if row.get('media_url') else ""
                
                title_html = f'<div class="card-title"><a href="{row["tweet_url"]}" target="_blank">{row["author"]}</a></div>' if row.get('tweet_url') else f'<div class="card-title">{row["author"]}</div>'
                
                # Topic Tag "None" gelmesini veya boş gelmesini engelle
                tag_label = row["topic_tag"] if row["topic_tag"] and str(row["topic_tag"]) != "None" else row["category"]
                if not tag_label.startswith("#"): tag_label = f"#{tag_label}"
                
                card_html = f'<div class="news-card">{media_html}{title_html}<div style="font-size:0.95rem; color:#000000; line-height:1.4;">{clickable_content}</div><div class="card-meta"><span>{row["processed_at"]}</span><span>{tag_label}</span></div></div>'
                st.markdown(card_html, unsafe_allow_html=True)
    
    if st.button("⬅️ Tüm Haberlere Dön"):
        set_page("Dashboard")
        st.rerun()
    st.stop()

# NORMAL DASHBOARD GÖRÜNÜMÜ (Scoopnest Dikey Kolon Düzeni)
# Veriyi Kategorilere Göre Hazırla
all_categories = ["Türkiye", "Dünya", "Ekonomi", "Teknoloji", "Spor", "Eğlence", "Müzik"]

# Sadece haber olan kategorileri göster (User Request: Boş kolonlar görünmesin)
visible_categories = [cat for cat in all_categories if not df[df['category'] == cat].empty]

if not visible_categories:
    st.info("Son 3 gün içinde henüz kategorize edilmiş haber bulunamadı.")
else:
    cols = st.columns(len(visible_categories))

    for i, category in enumerate(visible_categories):
        cat_df = df[df['category'] == category].head(15) # Dashboard başı 15 haber yeterli
        
        with cols[i]:
            # Kolon Başlığı
            st.markdown(f'<div class="column-header"><h3 style="font-size: 0.9rem;">{category}</h3><small>{len(cat_df)} Önemli Gelişme</small></div>', unsafe_allow_html=True)
            
            # Kolon İçeriği
            column_html = ""
            topics = cat_df.groupby('topic_tag')
            
            for tag, group in topics:
                # Deduplication: Aynı başlığı paylaşanları tek kartta göster
                display_news = group.iloc[0]
                content = display_news['content']
                
                # Başlık ve açıklama üretimi (Optimize edilmiş)
                if '.' in content:
                    news_title_raw = content.split('.')[0][:70]
                    news_desc_raw = content[len(news_title_raw)+1:200]
                else:
                    news_title_raw = content[:70]
                    news_desc_raw = content[70:200]
                
                news_title = news_title_raw + "..." if len(content) > 70 else content
                news_desc = news_desc_raw + "..." if len(content) > 200 else news_desc_raw
                
                media_html = f'<img src="{display_news["media_url"]}" style="width:100%; border-radius:12px; margin-bottom:10px; object-fit:cover; height:160px; background:#f1f5f9;">' if display_news.get('media_url') else ""
                
                # Tıklanabilir linkler (Hız için sadece title'a link veriyoruz)
                final_title = f'<a href="{display_news["tweet_url"]}" target="_blank" style="text-decoration:none; color:#1e40af;">{news_title}</a>' if display_news.get('tweet_url') else news_title
                
                extra_info = f'<div style="color:#2563eb; font-size:0.75rem; margin-top:5px; font-weight:600;">✨ {len(group)} Kaynak</div>' if len(group) > 1 else ""
                
                column_html += f"""
                <div class="news-card">
                    {media_html}
                    <div class="card-title" style="font-size:0.9rem; margin-bottom:5px;">{final_title}</div>
                    <div style="font-size:0.8rem; color:#475569; line-height:1.4;">{news_desc}</div>
                    <div class="card-meta">
                        <span>👤 {display_news["author"][:15]}</span>
                        <span>🕒 {display_news["processed_at"]}</span>
                        <span style="color:#2563eb; font-weight:700;">#{tag}</span>
                    </div>
                    {extra_info}
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
st.sidebar.caption("NucleusX Engine v15.0 Clean")
st.sidebar.caption("Developed by Antigravity AI 🤖")
