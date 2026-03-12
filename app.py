import streamlit as st
import re
import pandas as pd
import time
import html
from database import init_db, get_db_connection
from categorize_engine import run_categorization_process

# -----------------------------------------------------------------------------
# GLOBAL CONFIG & INITIALIZATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NucleusX AI V23.0 LUXURY",
    page_icon="🗞️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Canlı yayında veritabanı yoksa oluştur
init_db()

# V22.0 Cache Initialization
if 'init_v22_0' not in st.session_state:
    st.cache_data.clear()
    st.session_state.init_v22_0 = True

# -----------------------------------------------------------------------------
# STYLING (Responsive Dual-Core)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; box-sizing: border-box; }

    /* Streamlit Global Background */
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
            border-radius: 0px !important; /* Sharp corners for fintech look */
            padding: 0px;
            margin-bottom: 25px;
            box-shadow: 0 15px 35px rgba(37, 99, 235, 0.08); 
            transition: transform 0.2s ease;
            overflow: hidden;
        }
        .news-card-content { padding: 20px; }
        .card-title a { color: #000000 !important; font-weight: 800; font-size: 1.2rem; line-height: 1.3; text-decoration: none; }
        .card-desc { font-size: 0.95rem; color: #475569; margin-top: 10px; line-height: 1.5; }
        .card-meta { margin-top: 15px; padding-top: 15px; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 0.5px; }
        
        [data-testid="column"] { flex: 0 0 100% !important; min-width: 100% !important; margin-bottom: 20px; }
    }

    /* =======================================================
       PREMIUM LUXURY DESIGN (Scoopnest Inspired)
       ======================================================= */
    .stApp { background-color: #ffffff !important; }
    
    /* TOP NAV: PRO & CLEAN */
    .top-nav {
        display: flex; justify-content: space-between; align-items: center;
        padding: 20px 40px; background: #ffffff; border-bottom: 1px solid #e2e8f0;
        margin-left: -5rem; margin-right: -5rem; margin-top: -10px; margin-bottom: 30px;
    }
    .logo-text { font-weight: 900; font-size: 1.5rem; color: #000; letter-spacing: -0.5px; }
    .logo-text b { color: #1e3a8a; } /* Dark Blue Accent */

    /* SIDEBAR: LUXURY MINIMALISM */
    section[data-testid="stSidebar"] { 
        background-color: #ffffff !important; 
        border-right: 1px solid #e2e8f0 !important;
    }

    /* NEWS CARD: LUXURY TWIST */
    .news-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-top: 3px solid #6366f1; /* Subtle Indigo Border */
        border-radius: 4px;
        padding: 0px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); /* Soft Elevation */
        transition: all 0.25s ease;
        overflow: hidden;
    }
    .news-card:hover { 
        transform: translateY(-4px); 
        box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); 
        border-color: #6366f1;
    }

    /* TYPOGRAPHY: BOLD BLACK TITLES */
    .news-card-content { padding: 16px; }
    .card-title a { 
        color: #000000 !important; 
        font-weight: 800; 
        font-size: 1.05rem !important; 
        line-height: 1.35; 
        text-decoration: none;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-title a:hover { color: #4338ca !important; }
    
    .card-desc { 
        font-size: 0.85rem !important; 
        color: #4b5563; 
        margin-top: 10px; 
        line-height: 1.5; 
        display: -webkit-box; 
        -webkit-line-clamp: 2; 
        -webkit-box-orient: vertical; 
        overflow: hidden; 
    }
    
    .card-meta { 
        margin-top: 15px; 
        padding-top: 12px;
        border-top: 1px solid #f3f4f6;
        font-size: 0.7rem !important; 
        color: #6b7280; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* MULTI-COLUMN FEED OPTIMIZATION */
    [data-testid="stHorizontalBlock"] { gap: 20px !important; }
    [data-testid="column"] { flex: 0 0 320px !important; min-width: 320px !important; }
    
    .column-header { 
        padding: 0 0 10px 0;
        margin-bottom: 20px; 
        border-bottom: 2px solid #000;
    }
    .column-header h3 { 
        color: #000000 !important; 
        font-size: 0.9rem !important; 
        margin: 0 !important; 
        font-weight: 900 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* INTERACTION ELEMENTS: DARK BLUE */
    div.stButton > button {
        border-radius: 4px !important;
        background-color: #f8fafc !important;
        color: #1e3a8a !important;
        border: 1px solid #e2e8f0 !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    div.stButton > button:hover {
        background-color: #1e3a8a !important;
        color: #ffffff !important;
        border-color: #1e3a8a !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def get_card_html(row, cat_name_override=None):
    """Generates standardized HTML for a news card (Escaped & Sanitized)."""
    content_raw = str(row.get('content', '')).replace("\n", " ")
    
    # Robust Title/Desc Split (Luxury Limits)
    if '.' in content_raw and len(content_raw.split('.')[0]) > 10:
        parts = content_raw.split('.')
        news_title = parts[0].strip()[:100]
        news_desc = ".".join(parts[1:]).strip()[:120]
    else:
        news_title = content_raw[:100]
        news_desc = content_raw[100:200]
    
    if len(content_raw) > len(news_title): news_title += "..."
    if len(news_desc) > 0 and len(content_raw) > (len(news_title) + 5): news_desc += "..."
    
    # Escape for HTML safety
    news_title = html.escape(news_title)
    news_desc = html.escape(news_desc)
    author_name = html.escape(str(row.get('author') or 'ANONYMOUS')).upper()
    processed_at = html.escape(str(row.get('processed_at', '00:00')))
    tweet_url = row.get('tweet_url', '#')
    media_url = row.get('media_url')
    
    cat_val = cat_name_override or row.get('category', 'HABER')
    cat_class = f"cat-{cat_val.lower().replace('ü', 'u').replace('ö', 'o').replace('ı', 'i').replace('ş', 's').replace('ç', 'c')}"

    media_html = f'<div style="width:100%; height:160px; overflow:hidden;"><img src="{media_url}" style="width:100%; height:100%; object-fit:cover;"></div>' if media_url else ""
    title_html = f'<a href="{tweet_url}" target="_blank">{news_title}</a>'
    
    return f'<div class="news-card {cat_class}">{media_html}<div class="news-card-content"><div class="card-title">{title_html}</div><div class="card-desc">{news_desc}</div><div class="card-meta"><span>{author_name}</span><div class="sparkline"></div><span>{processed_at}</span></div></div></div>'

@st.cache_data(ttl=600)
def load_data():
    try:
        conn = get_db_connection()
        query = "SELECT author, content, category, topic_tag, processed_at, media_url, tweet_url FROM tweets WHERE processed_at > NOW() - INTERVAL '7 days' ORDER BY processed_at DESC LIMIT 500"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if not df.empty:
            df['processed_at'] = pd.to_datetime(df['processed_at']).dt.strftime('%H:%M')
            df['topic_tag'] = df['topic_tag'].fillna('HABER').str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"Veritabanı Hatası: {e}")
        return pd.DataFrame(columns=['author', 'content', 'category', 'topic_tag', 'processed_at', 'media_url', 'tweet_url'])

# -----------------------------------------------------------------------------
# APP LOGIC
# -----------------------------------------------------------------------------
df = load_data()

# Navigation Items
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

# Sidebar
with st.sidebar:
    st.markdown("### NUCLEUS X")
    st.markdown("---")
    
    # Nav Buttons
    for item in nav_items:
        is_active = st.session_state.get('current_page', 'Dashboard') == item["name"]
        
        # High contrast Luxury state
        if is_active:
            st.markdown(f'''<style>div[data-testid="stSidebar"] div.stButton > button[key="nav_{item['name']}"] {{ background: #1e3a8a !important; color: #ffffff !important; font-weight: 800 !important; border: none !important; }}</style>''', unsafe_allow_html=True)
        else:
            st.markdown(f'''<style>div[data-testid="stSidebar"] div.stButton > button[key="nav_{item['name']}"] {{ background: #ffffff !important; color: #1e1e1e !important; font-weight: 600 !important; border-bottom: 1px solid #f1f5f9 !important; border-radius: 0 !important; text-align: left !important; }}</style>''', unsafe_allow_html=True)
        
        if st.button(item['label'], key=f"nav_{item['name']}", use_container_width=True):
            st.session_state.current_page = item["name"]
            st.session_state.selected_tag = None
            st.rerun()
            
    st.markdown("---")
    with st.expander("Yönetici Paneli"):
        admin_password = st.text_input("Şifre", type="password")
        ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "nucleus123")
        
        if st.button("Haberleri Tara"):
            if admin_password == ADMIN_PASS:
                status_text = st.empty()
                with st.spinner("Taranıyor..."):
                    for update in run_categorization_process():
                        status_text.info(update)
                    st.success("Bitti.")
                    st.rerun()
            else: st.error("Yetkisiz.")

# Top Nav
st.markdown(f"""
    <div class="top-nav">
        <div class="logo-text">NUCLEUS<b>X</b> AI <small style="font-weight:400; font-size:0.6rem; opacity:0.6;">v22.0</small></div>
        <div style="display:flex; gap:15px; align-items:center;">
            <div style="width:10px; height:10px; background:#22c55e; border-radius:50%; box-shadow:0 0 10px #22c55e;"></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Main Navigation Router
current_page = st.session_state.get('current_page', 'Dashboard')
selected_tag = st.session_state.get('selected_tag')

if selected_tag:
    # Tag View
    st.markdown(f"### #{selected_tag} Gelişmeleri")
    tag_df = df[df['topic_tag'] == selected_tag]
    if not tag_df.empty:
        t_cols = st.columns(3)
        for idx, row in tag_df.iterrows():
            with t_cols[idx % 3]:
                st.markdown(get_card_html(row), unsafe_allow_html=True)
    if st.button("Geri Dön"):
        st.session_state.selected_tag = None
        st.rerun()
    st.stop()

if current_page != "Dashboard":
    # Category Detail View
    cat_label = next((i['label'] for i in nav_items if i['name'] == current_page), current_page)
    st.markdown(f'<div class="detail-view"><h2>{cat_label}</h2></div>', unsafe_allow_html=True)
    
    cat_df = df[df['category'] == current_page].head(60)
    if not cat_df.empty:
        grid = st.columns(3)
        for idx, row in cat_df.iterrows():
            with grid[idx % 3]:
                st.markdown(get_card_html(row), unsafe_allow_html=True)
    else:
        st.info("Bu kategoride henüz haber yok.")
    
    if st.button("Ana Sayfa"):
        st.session_state.current_page = "Dashboard"
        st.rerun()
    st.stop()

# Dashboard View
if current_page == "Dashboard":
    # Trending Pills
    if not df.empty:
        pop_tags = df[~df['topic_tag'].isin(["#HABER", "#GUNDEM", "#DETAY"])]['topic_tag'].value_counts().head(7).index.tolist()
        if pop_tags:
            pill_cols = st.columns(len(pop_tags))
            for i, pt in enumerate(pop_tags):
                if pill_cols[i].button(pt, key=f"p_{pt}", use_container_width=True):
                    st.session_state.selected_tag = pt
                    st.rerun()

    # Multi Column Feed
    all_cats = ["Türkiye", "Dünya", "Ekonomi", "Teknoloji", "Spor", "Eğlence", "Müzik"]
    visible_cats = [c for c in all_cats if not df[df['category'] == c].empty]
    
    if visible_cats:
        d_cols = st.columns(len(visible_cats))
        for i, cat in enumerate(visible_cats):
            with d_cols[i]:
                st.markdown(f'<div class="column-header"><h3>{cat}</h3></div>', unsafe_allow_html=True)
                cat_df = df[df['category'] == cat].head(15)
                # Group by topic tag to avoid duplicates in the same column
                topics = cat_df.groupby('topic_tag')
                col_html = ""
                for t, group in topics:
                    col_html += get_card_html(group.iloc[0]).strip() + "\n"
                st.markdown(col_html, unsafe_allow_html=True)
    else:
        st.warning("Henüz haber verisi bulunmuyor. Lütfen yönetici panelinden tarama yapın.")

st.sidebar.markdown("---")
st.sidebar.caption("NucleusX V22.0 Ultimate - Developed by Antigravity AI")
