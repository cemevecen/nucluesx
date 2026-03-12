import streamlit as st
import re
import pandas as pd
from database import init_db, get_db_connection
import time
from categorize_engine import run_categorization_process

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="NucleusX AI V19.0 HYBRID",
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

    /* Ana Arka Plan - Luxury White */
    .stApp {
        background-color: #ffffff !important;
    }
    
    /* Header (Top Nav) - Premium Luxury */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 30px;
        background: #ffffff;
        border-bottom: 2px solid #f1f5f9;
        position: sticky;
        top: 0;
        z-index: 1000;
        margin-bottom: 30px;
        margin-top: -10px;
        margin-left: calc(-1 * min(5rem, 5vw));
        margin-right: calc(-1 * min(5rem, 5vw));
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }
    .logo-text {
        font-weight: 900;
        font-size: 1.4rem;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    .logo-text b { color: #1e3a8a; }
    
    .search-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 10px 20px;
        border-radius: 30px;
        flex: 1;
        max-width: 500px;
        margin: 0 40px;
        color: #64748b;
        font-size: 0.85rem;
    }

    /* Sidebar - Luxury Clean */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #f1f5f9 !important;
    }
    
    /* News Cards - Luxury Hybrid Style */
    .news-card {
        background: #ffffff !important;
        border: 1px solid #e0e7ff; /* Subtle Indigo */
        border-radius: 1px; /* Sharper, more editorial feel */
        padding: 0px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        overflow: hidden;
    }
    .news-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.08);
        border-color: #c7d2fe;
    }
    .news-card-content {
        padding: 15px;
    }
    .card-title {
        color: #000000 !important;
        font-weight: 800;
        font-size: 1.1rem;
        line-height: 1.3;
        margin-bottom: 8px;
        letter-spacing: -0.2px;
    }
    .card-meta {
        color: #64748b !important;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: flex;
        justify-content: space-between;
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid #f8fafc;
    }
    
    /* Multi-Column Layout (Scoopnest Feed) */
    .column-header {
        border-top: 3px solid #1e3a8a;
        padding: 15px 0;
        margin-bottom: 15px;
    }
    .column-header h3 {
        color: #0f172a !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .column-header small {
        color: #64748b;
        font-size: 0.75rem;
    }

    /* Horizontal Scroll Logic - Optimized */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        gap: 15px !important;
        padding: 5px !important;
        -webkit-overflow-scrolling: touch;
    }
    
    [data-testid="column"] {
        flex: 0 0 320px !important;
        min-width: 320px !important;
        max-width: 320px !important;
    }
    
    /* Global Card Responsive Styles */
    @media (max-width: 768px) {
        [data-testid="column"] {
            flex: 0 0 88% !important;
            min-width: 88% !important;
        }
        .top-nav { margin-left: -1rem; margin-right: -1rem; }
    }
    
    /* Ensure detail pages (vertical stack) are not forced horizontal */
    .detail-view [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        overflow-x: visible !important;
    }
    .detail-view [data-testid="column"] {
        flex: 1 1 30% !important;
        min-width: 300px !important;
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
print("--- !!! TITAN V19.0 PREMIUM HYBRID DEPLOY !!! ---")

# Canlıda cache'i temizle
if 'init_v19_0' not in st.session_state:
    st.cache_data.clear()
    st.session_state.init_v19_0 = True

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
        border: 1px solid #2563eb !important;
        border-radius: 30px !important;
        background: #e0f2fe !important;
        color: #1e40af !important;
        height: 40px !important;
        font-weight: 600 !important;
    }
    div.stButton > button:first-child[key^="t_"]:hover {
        background: #d0effc !important;
        border-color: #1e40af !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sticky Top Nav (Logo & Search)
st.markdown("""
    <div class="top-nav">
        <div class="logo-text">
            NUCLEUS <b>X</b> <span style="font-size: 0.7rem; opacity: 0.4;">v19.0 HYBRID</span>
        </div>
        <div class="search-box"> Haberlerde anahtar kelime ile ara...</div>
        <div style="display: flex; gap: 15px; align-items: center;">
            <span style="background: #1e3a8a; color: white; padding: 6px 16px; border-radius: 4px; font-size: 0.7rem; font-weight: 900; letter-spacing: 1px;">LIVE FEED</span>
            <div style="width: 32px; height: 32px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: bold; color: #1e3a8a; border: 1px solid #e2e8f0;">AX</div>
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
                    background-color: #2563eb !important;
                    color: white !important;
                    border: none !important;
                    font-weight: 700 !important;
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
            tag_cols[-1].button("Reset", on_click=clear_tag)

st.markdown("<br>", unsafe_allow_html=True)

# FİLTRELİ KONU GÖRÜNÜMÜ
if st.session_state.selected_tag:
    st.markdown(f"### [TAG] {st.session_state.selected_tag} Hakkındaki Tüm Gelişmeler")
    tag_df = df[df['topic_tag'] == st.session_state.selected_tag]
    
    tag_cols = st.columns(3)
    for idx, row in tag_df.iterrows():
        with tag_cols[idx % 3]:
            clickable_content = make_clickable(row['content'])
            media_html = f'<img src="{row["media_url"]}" style="width:100%; border-radius:12px; margin-bottom:12px; object-fit:cover; height:220px; background:#f1f5f9;">' if row.get('media_url') else ""
            
            # Başlığa Tıklandığında Twite Gitme Özelliği
            title_html = f'<div class="card-title"><a href="{row["tweet_url"]}" target="_blank">{row["author"]}</a></div>' if row.get('tweet_url') else f'<div class="card-title">{row["author"]}</div>'
            
            card_html = f'<div class="news-card">{media_html}{title_html}<div style="font-size:0.95rem; line-height:1.4;">{clickable_content}</div><div class="card-meta"><span>SAAT: {row["processed_at"]}</span><span style="color:#2563eb;">{row["category"]}</span></div></div>'
            st.markdown(card_html, unsafe_allow_html=True)
    
    if st.button("Ana Sayfaya Dön", on_click=clear_tag):
        st.rerun()
    st.stop()

# ANA İÇERİK MANTİĞİ
if st.session_state.current_page != "Dashboard":
    # TEK KATEGORİ GÖRÜNÜMÜ - ÖZEL SAYFA
    cat_name = st.session_state.current_page
    # Başlığı bulalım
    cat_label = next((item["label"] for item in nav_items if item["name"] == cat_name), cat_name)
    
    cat_icons = {
        "Dashboard": "", "Türkiye": "", "Ekonomi": "", 
        "Teknoloji": "", "Spor": "", "Dünya": "", 
        "Eğlence": "", "Müzik": ""
    }
    icon = cat_icons.get(cat_name, "")

    st.markdown(f"""
        <div class="detail-view" style="padding: 15px; background: white; border-bottom: 2px solid #3b82f6; border-radius: 12px; margin-bottom: 25px;">
            <h2 style="margin: 0; color: #1e293b; font-size: 1.5rem;">{icon} {cat_label}</h2>
            <p style="margin: 5px 0 0 0; color: #64748b; font-size: 0.85rem;">En son {cat_label} haberleri ve gelişmeleri.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Detail View Wrapper Start point
    st.markdown('<div class="detail-view">', unsafe_allow_html=True)
    
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
                
                card_html = f'<div class="news-card">{media_html}{title_html}<div style="font-size:0.95rem; line-height:1.4; color: #1e293b;">{clickable_content}</div><div class="card-meta"><span>SAAT: {row["processed_at"]}</span><span style="color:#2563eb;">{tag_label}</span></div></div>'
                st.markdown(card_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True) # Detail View Wrapper End
    
    if st.button("Tüm Haberlere Dön"):
        set_page("Dashboard")
        st.rerun()
    st.stop()

# NORMAL DASHBOARD GÖRÜNÜMÜ (Scoopnest Dikey Kolon Düzeni)
# Veriyi Kategorilere Göre Hazırla
all_categories = ["Türkiye", "Dünya", "Ekonomi", "Teknoloji", "Spor", "Eğlence", "Müzik"]

# Sadece haber olan kategorileri göster (User Request: Boş kolonlar görünmesin)
visible_categories = [cat for cat in all_categories if not df[df['category'] == cat].empty]

# Kategori İkonları (İçerik için)
cat_icons = {
    "Dashboard": "", "Türkiye": "", "Ekonomi": "", 
    "Teknoloji": "", "Spor": "", "Dünya": "", 
    "Eğlence": "", "Müzik": ""
}

# --- ANA SAYFA (GRID GÖRÜNÜMÜ) ---
if st.session_state.current_page == "Dashboard":
    cols = st.columns(len(visible_categories))
    for i, category in enumerate(visible_categories):
        cat_df = df[df['category'] == category].head(15) if not df.empty else pd.DataFrame()
        
        with cols[i]:
            # Kolon Başlığı
            icon = cat_icons.get(category, "")
            st.markdown(f'<div class="column-header"><h3>{category}</h3></div>', unsafe_allow_html=True)
            
            # Kolon İçeriği
            column_html = ""
            topics = cat_df.groupby('topic_tag')
            
            for tag, group in topics:
                # Deduplication: Aynı başlığı paylaşanları tek kartta göster
                display_news = group.iloc[0]
                content = display_news['content']
                
                # Başlık ve açıklama üretimi (Geliştirilmiş Split)
                content_clean = content.replace("\n", " ")
                if '.' in content_clean:
                    parts = content_clean.split('.')
                    news_title_raw = parts[0].strip()[:80]
                    news_desc_raw = ".".join(parts[1:]).strip()[:150]
                else:
                    news_title_raw = content_clean[:80]
                    news_desc_raw = content_clean[80:200]
                
                news_title = news_title_raw + "..." if len(content_clean) > 80 and not news_title_raw.endswith("...") else news_title_raw
                news_desc = news_desc_raw + "..." if len(content_clean) > len(news_title_raw) + 10 else news_desc_raw
                
                media_html = f'<img src="{display_news["media_url"]}" style="width:100%; border-radius:12px; margin-bottom:10px; object-fit:cover; height:160px; background:#f1f5f9;">' if display_news.get('media_url') else ""
                
                # Tıklanabilir linkler (Hız için sadece title'a link veriyoruz)
                final_title = f'<a href="{display_news["tweet_url"]}" target="_blank" style="text-decoration:none; color:#1e40af;">{news_title}</a>' if display_news.get('tweet_url') else news_title
                
                extra_info = f'<div style="color:#2563eb; font-size:0.75rem; margin-top:5px; font-weight:600;">{len(group)} Kaynak</div>' if len(group) > 1 else ""
                
                author_name = (display_news.get('author') or 'Anonim')[:25]
                card_html = f'''
                <div class="news-card">
                    {media_html}
                    <div class="news-card-content">
                        <div class="card-title">{final_title}</div>
                        <div style="font-size:0.85rem; color:#475569; line-height:1.5;">{news_desc}</div>
                        <div class="card-meta">
                            <span>{author_name}</span>
                            <span style="color:#1e3a8a;">#{tag if str(tag).startswith("#") else f"{tag}"}</span>
                        </div>
                        {extra_info}
                    </div>
                </div>
                '''
                column_html += card_html.strip()
            
            st.markdown(column_html, unsafe_allow_html=True)

# Manuel Yenileme Butonu (Test İçin Sınırsız, Ancak Kota Dostu)
if st.sidebar.button("Şimdi Yeni Haberleri Tara"):
    # 1. Şifre Kontrolü
    if admin_password != ADMIN_PASS:
        st.sidebar.error("Hatalı şifre! Tarama izniniz yok.")
    else:
        # Motor artık adım adım (generator) çalıştığı için döngüyle bildirim alıyoruz
        status_text = st.sidebar.empty()
        with st.spinner("NucleusX AI Haberleri Topluyor..."):
            try:
                for update in run_categorization_process():
                    status_text.info(update.replace("🚀", "").replace("✅", "").replace("🧹", "").replace("♻️", ""))
                st.success("Tarama tamamlandı! Sayfa yenileniyor...")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Tarama sırasında bir hata oluştu: {e}")

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
    
    yield f"{len(rows)} haber için derin analiz başlıyor..."
    
    for row_id, content in rows:
        cat, tag = get_full_analysis(content)
        cursor.execute("UPDATE tweets SET category = %s, topic_tag = %s WHERE id = %s", (cat, tag, row_id))
        conn.commit()
        yield f"{tag} [{cat}] (ID: {row_id})"
    
    conn.close()
    yield "Veritabanı başarıyla optimize edildi!"

# MİGRASYON / BAKIM BUTONU
if st.sidebar.button("Tüm Veritabanını Optimize Et"):
    if admin_password != ADMIN_PASS:
        st.sidebar.error("Yönetici yetkisi gerekli.")
    else:
        status_text = st.sidebar.empty()
        with st.spinner("Eski haberler kümeleniyor..."):
            try:
                for log in recategorize_all_news():
                    status_text.info(log)
                # Önbelleği temizleyelim ki yeni hashtagler hemen gelsin
                st.cache_data.clear()
                st.success("Tüm geçmiş veriler optimize edildi!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Optimizasyon hatası: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("NucleusX Engine v19.0 Hybrid")
st.sidebar.caption("Developed by Antigravity AI")
