import streamlit as st
import re
import pandas as pd
from database import init_db, get_db_connection
import time
from categorize_engine import run_categorization_process

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="NucleusX AI V21.0 DUAL-CORE",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Canlı yayında veritabanı yoksa oluştur
init_db()

# Premium CSS - DUAL CORE DYNAMIC DESIGN
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; box-sizing: border-box; }

    /* Streamlit Background Fix */
    .stApp { background-color: #ffffff !important; }

    /* COMMON NAV (Responsive) */
    .top-nav {
        display: flex; justify-content: space-between; align-items: center;
        padding: 15px 25px; background: #ffffff; border-bottom: 2px solid #f1f5f9;
        margin-left: -5rem; margin-right: -5rem; margin-top: -10px; margin-bottom: 20px;
    }
    .logo-text { font-weight: 800; font-size: 1.3rem; color: #000; }
    .logo-text b { color: #2563eb; }

    /* =======================================================
       MOBILE DESIGN: SLEEK FINTECH (Max 991px)
       ======================================================= */
    @media (max-width: 991px) {
        .stApp { background-color: #ffffff !important; }
        .top-nav { margin-left: -1rem; margin-right: -1rem; padding: 10px 15px; background: #2563eb; border: none; }
        .logo-text { color: #ffffff !important; }
        .logo-text b { color: #ffffff !important; opacity: 0.8; }
        
        .news-card {
            background: #ffffff !important;
            border: 1px solid #f1f5f9;
            border-radius: 0px !important; /* Sharp corners */
            padding: 0px;
            margin-bottom: 25px;
            box-shadow: 0 15px 35px rgba(37, 99, 235, 0.08); /* Soft blue shadow */
            transition: transform 0.2s ease;
        }
        .news-card-content { padding: 20px; }
        .card-title a { color: #000000 !important; font-weight: 800; font-size: 1.2rem; line-height: 1.3; text-decoration: none; }
        .card-desc { font-size: 0.95rem; color: #475569; margin-top: 10px; line-height: 1.5; }
        .card-meta { margin-top: 15px; padding-top: 15px; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Column stacking for mobile */
        [data-testid="column"] { flex: 0 0 100% !important; min-width: 100% !important; margin-bottom: 20px; }
    }

    /* =======================================================
       WEB DESIGN: DYNAMIC DASHBOARD (Min 992px)
       ======================================================= */
    @media (min-width: 992px) {
        .stApp { background-color: #f8fafc !important; }
        
        /* Sidebar dark theme */
        section[data-testid="stSidebar"] { background-color: #0f172a !important; color: white !important; }
        section[data-testid="stSidebar"] .stMarkdown p, section[data-testid="stSidebar"] .stHeader { color: white !important; }
        
        /* Compact Data-Rich Cards */
        .news-card {
            background: #ffffff !important;
            border-radius: 6px;
            padding: 0px;
            margin-bottom: 12px;
            border-left: 4px solid #2563eb; /* Vertical Indicator */
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }
        .news-card:hover { transform: scale(1.02); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        
        /* Dynamic Category Indicators */
        .cat-turkiye { border-left-color: #ef4444; } /* Red */
        .cat-ekonomi { border-left-color: #10b981; } /* Green */
        .cat-teknoloji { border-left-color: #3b82f6; } /* Blue */
        .cat-dunya { border-left-color: #f59e0b; } /* Orange */
        
        .news-card-content { padding: 12px; }
        .card-title a { color: #1e293b !important; font-weight: 700; font-size: 0.85rem; line-height: 1.4; text-decoration: none; }
        .card-desc { font-size: 0.75rem; color: #64748b; margin-top: 5px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        
        .card-meta { margin-top: 8px; font-size: 0.65rem; color: #94a3b8; display: flex; justify-content: space-between; align-items: center; }
        
        /* Simulated Sparkline for "Activity" */
        .sparkline { width: 40px; height: 15px; background: linear-gradient(90deg, #e2e8f0 25%, #2563eb 50%, #e2e8f0 75%); border-radius: 2px; opacity: 0.5; }

        /* Multi-Column Feed Arrangement */
        [data-testid="stHorizontalBlock"] { gap: 10px !important; }
        [data-testid="column"] { flex: 0 0 280px !important; min-width: 280px !important; }
        
        .column-header { background: #1e293b; color: white; padding: 10px; border-radius: 4px; margin-bottom: 10px; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
        .column-header h3 { color: white !important; font-size: 0.75rem !important; margin: 0 !important; }
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
print("--- !!! NUCLEUS X V21.0 DUAL-CORE DEPLOY !!! ---")

# Canlıda cache'i temizle
if 'init_v21_0' not in st.session_state:
    st.cache_data.clear()
    st.session_state.init_v21_0 = True

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
        <div class="logo-text">NUCLEUS<b>X</b> AI <small style="font-weight:400; font-size:0.6rem; opacity:0.6;">v21.0</small></div>
        <div style="display:flex; gap:15px; align-items:center;">
            <span style="font-size:0.7rem; font-weight:700; color:#94a3b8; letter-spacing:1px;" class="mobile-hide">SYSTEM STATUS: ONLINE</span>
            <div style="width:10px; height:10px; background:#22c55e; border-radius:50%; box-shadow:0 0 10px #22c55e;"></div>
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
            # Başlık ve açıklama üretimi (ROBUST SPLIT)
            content_clean = row['content'].replace("\n", " ")
            if '.' in content_clean and len(content_clean.split('.')[0]) > 10:
                parts = content_clean.split('.')
                news_title = parts[0].strip()[:80]
                news_desc = ".".join(parts[1:]).strip()[:200]
            else:
                news_title = content_clean[:80]
                news_desc = content_clean[80:250]
            
            if len(content_clean) > len(news_title): news_title += "..."
            if len(news_desc) > 0 and len(content_clean) > (len(news_title) + 5): news_desc += "..."

            media_html = f'<div style="width:100%; height:180px; overflow:hidden;"><img src="{row["media_url"]}" style="width:100%; height:100%; object-fit:cover;"></div>' if row.get('media_url') else ""
            title_html = f'<a href="{row["tweet_url"]}" target="_blank">{news_title}</a>' if row.get('tweet_url') else news_title
            
            author_name = (row.get('author') or 'ANONYMOUS').upper()
            
            card_html = f'''
            <div class="news-card">
                {media_html}
                <div class="news-card-content">
                    <div class="card-title">{title_html}</div>
                    <div class="card-desc">{news_desc}</div>
                    <div class="card-meta">
                        <span>{author_name}</span>
                        <div class="sparkline"></div>
                        <span>{row["processed_at"]}</span>
                    </div>
                </div>
            </div>
            '''
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
                # Başlık ve açıklama üretimi (ROBUST SPLIT)
                content_clean = row['content'].replace("\n", " ")
                if '.' in content_clean and len(content_clean.split('.')[0]) > 10:
                    parts = content_clean.split('.')
                    news_title = parts[0].strip()[:80]
                    news_desc = ".".join(parts[1:]).strip()[:200]
                else:
                    news_title = content_clean[:80]
                    news_desc = content_clean[80:250]
                
                if len(content_clean) > len(news_title): news_title += "..."
                if len(news_desc) > 0 and len(content_clean) > (len(news_title) + 5): news_desc += "..."

                media_html = f'<div style="width:100%; height:180px; overflow:hidden;"><img src="{row["media_url"]}" style="width:100%; height:100%; object-fit:cover;"></div>' if row.get('media_url') else ""
                title_html = f'<a href="{row["tweet_url"]}" target="_blank">{news_title}</a>' if row.get('tweet_url') else news_title
                
                author_name = (row.get('author') or 'ANONYMOUS').upper()
                
                card_html = f'''
                <div class="news-card">
                    {media_html}
                    <div class="news-card-content">
                        <div class="card-title">{title_html}</div>
                        <div class="card-desc">{news_desc}</div>
                        <div class="card-meta">
                            <span>{author_name}</span>
                            <div class="sparkline"></div>
                            <span>{row["processed_at"]}</span>
                        </div>
                    </div>
                </div>
                '''
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
                display_news = group.iloc[0]
                content = display_news['content']
                
                # Başlık ve açıklama üretimi (ROBUST SPLIT)
                content_clean = content.replace("\n", " ")
                if '.' in content_clean and len(content_clean.split('.')[0]) > 10:
                    parts = content_clean.split('.')
                    news_title = parts[0].strip()[:80]
                    news_desc = ".".join(parts[1:]).strip()[:150]
                else:
                    news_title = content_clean[:80]
                    news_desc = content_clean[80:200]
                
                if len(content_clean) > len(news_title): news_title += "..."
                if len(news_desc) > 0 and len(content_clean) > (len(news_title) + 5): news_desc += "..."
                
                media_html = f'<div style="width:100%; height:140px; overflow:hidden;"><img src="{display_news["media_url"]}" style="width:100%; height:100%; object-fit:cover;"></div>' if display_news.get('media_url') else ""
                title_html = f'<a href="{display_news["tweet_url"]}" target="_blank">{news_title}</a>' if display_news.get('tweet_url') else news_title
                
                cat_class = f"cat-{category.lower().replace('ü', 'u').replace('ö', 'o').replace('ı', 'i').replace('ş', 's').replace('ç', 'c')}"
                author_name = (display_news.get('author') or 'ANONYMOUS').upper()
                
                card_html = f'''
                <div class="news-card {cat_class}">
                    {media_html}
                    <div class="news-card-content">
                        <div class="card-title">{title_html}</div>
                        <div class="card-desc">{news_desc}</div>
                        <div class="card-meta">
                            <span>{author_name}</span>
                            <div class="sparkline"></div>
                            <span>{display_news["processed_at"]}</span>
                        </div>
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
st.sidebar.caption("NucleusX Engine v21.0 Dual-Core")
st.sidebar.caption("Developed by Antigravity AI")
