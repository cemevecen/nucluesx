import streamlit as st
import re
import pandas as pd
import time
import html
from database import init_db, get_db_connection
from categorize_engine import run_categorization_process
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# GLOBAL CONFIG & INITIALIZATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NucleusX AI V38.6 LUXURY",
    page_icon="🗞️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def slugify(text):
    """Turkish to English slug converter."""
    char_map = str.maketrans("çğıöşü ", "cgiosu-")
    return text.lower().translate(char_map).replace(" ", "-")

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
        padding: 15px 25px; background: #f1f5f9 !important; border-bottom: 2px solid #e2e8f0;
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

    /* NAV TABS: SCROLLABLE BAR */
    .nav-tabs-wrapper {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        gap: 10px !important;
        padding: 5px 40px 15px 40px !important;
        background: #f8fafc !important;
        border-bottom: 1px solid #f1f5f9;
        margin-left: -5rem; margin-right: -5rem;
        margin-top: -20px;
        margin-bottom: 25px;
        scrollbar-width: none; /* Hide for clean look */
    }
    .nav-tabs-wrapper::-webkit-scrollbar { display: none; }
    
    .nav-tab-item {
        flex: 0 0 auto !important;
        padding: 8px 20px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        color: #475569;
        font-weight: 700;
        font-size: 0.85rem;
        text-decoration: none;
        white-space: nowrap;
        transition: all 0.25s;
        cursor: pointer;
    }
    
    /* V32.0 Functional Links */
    .nav-tab-item { text-decoration: none !important; color: inherit; display: inline-block; }
    .nav-tab-item.tab-turkiye { color: #fca5a5; border-color: #fca5a5; }
    .nav-tab-item.tab-turkiye.active, .nav-tab-item.tab-turkiye:hover { background: #fca5a5 !important; color: #ffffff !important; }
    
    .nav-tab-item.tab-ekonomi { color: #fde047; border-color: #fde047; }
    .nav-tab-item.tab-ekonomi.active, .nav-tab-item.tab-ekonomi:hover { background: #fde047 !important; color: #78350f !important; }
    
    .nav-tab-item.tab-spor { color: #86efac; border-color: #86efac; }
    .nav-tab-item.tab-spor.active, .nav-tab-item.tab-spor:hover { background: #86efac !important; color: #14532d !important; }
    
    .nav-tab-item.tab-muzik { color: #c4b5fd; border-color: #c4b5fd; }
    .nav-tab-item.tab-muzik.active, .nav-tab-item.tab-muzik:hover { background: #c4b5fd !important; color: #ffffff !important; }
    
    .nav-tab-item.tab-teknoloji { color: #93c5fd; border-color: #93c5fd; }
    .nav-tab-item.tab-teknoloji.active, .nav-tab-item.tab-teknoloji:hover { background: #93c5fd !important; color: #ffffff !important; }
    
    .nav-tab-item.tab-dunya { color: #a8a29e; border-color: #d6d3d1; }
    .nav-tab-item.tab-dunya.active, .nav-tab-item.tab-dunya:hover { background: #d6d3d1 !important; color: #ffffff !important; }
    
    .nav-tab-item.tab-eglence { color: #fdba74; border-color: #fdba74; }
    .nav-tab-item.tab-eglence.active, .nav-tab-item.tab-eglence:hover { background: #fdba74 !important; color: #7c2d12 !important; }
    
    /* Dashboard button fallback */
    .nav-tab-item.tab-dashboard.active { background: #1e3a8a; color: #ffffff; border-color: #1e3a8a; }

    /* DASHBOARD GRID: ROCK SOLID V26.0 */
    .dashboard-wrapper {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        gap: 25px !important;
        padding: 10px 0 40px 0 !important;
        width: 100% !important;
        scroll-behavior: smooth;
        scrollbar-width: none; /* Firefox: Hide scrollbar */
    }
    .dashboard-wrapper::-webkit-scrollbar { display: none; } /* Chrome/Safari: Hide scrollbar */
    
    .category-column { 
        flex: 0 0 350px !important; /* Fixed width to prevent squeezing */
        min-width: 350px !important;
        max-width: 350px !important;
        flex-shrink: 0 !important;
    }
    
    /* V28.0 Pastel Category Colors */
    .cat-turkiye { border-top-color: #fca5a5 !important; } /* Pastel Kırmızı */
    .cat-ekonomi { border-top-color: #fde047 !important; } /* Pastel Sarı */
    .cat-muzik { border-top-color: #c4b5fd !important; }    /* Pastel Eflatun */
    .cat-dunya { border-top-color: #d6d3d1 !important; }   /* Pastel Kahverengi */
    .cat-teknoloji { border-top-color: #93c5fd !important; } /* Pastel Mavi */
    .cat-spor { border-top-color: #86efac !important; }      /* Pastel Yeşil */
    .cat-eglence { border-top-color: #fdba74 !important; }  /* Pastel Turuncu */

    /* Category Specific Hover Glows (Soft Pastel) */
    .news-card.cat-turkiye:hover { box-shadow: 0 15px 30px rgba(252, 165, 165, 0.25) !important; border-color: #fca5a5 !important; }
    .news-card.cat-ekonomi:hover { box-shadow: 0 15px 30px rgba(253, 224, 71, 0.25) !important; border-color: #fde047 !important; }
    .news-card.cat-muzik:hover { box-shadow: 0 15px 30px rgba(196, 181, 253, 0.25) !important; border-color: #c4b5fd !important; }
    .news-card.cat-dunya:hover { box-shadow: 0 15px 30px rgba(214, 211, 209, 0.25) !important; border-color: #d6d3d1 !important; }
    .news-card.cat-teknoloji:hover { box-shadow: 0 15px 30px rgba(147, 197, 253, 0.25) !important; border-color: #93c5fd !important; }
    .news-card.cat-spor:hover { box-shadow: 0 15px 30px rgba(134, 239, 172, 0.25) !important; border-color: #86efac !important; }
    .news-card.cat-eglence:hover { box-shadow: 0 15px 30px rgba(253, 186, 116, 0.25) !important; border-color: #fdba74 !important; }

    @media (max-width: 1400px) {
        .category-column { flex: 0 0 320px !important; min-width: 320px !important; }
    }
    @media (max-width: 768px) {
        .category-column { flex: 0 0 85vw !important; min-width: 85vw !important; }
    }
    
    /* Fixed V35.1 - Removed white override */
    .logo-text { font-weight: 900; font-size: 1.5rem; color: #000; letter-spacing: -0.5px; }
    .logo-text b { color: #1e3a8a; }

    /* SIDEBAR: LUXURY MINIMALISM */
    section[data-testid="stSidebar"] { 
        background-color: #ffffff !important; 
        border-right: 1px solid #e2e8f0 !important;
    }

    /* NEWS CARD: LUXURY TWIST */
    .news-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-top: 3px solid #6366f1; /* Default/Fallback */
        border-radius: 4px;
        padding: 0px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.25s ease;
        overflow: hidden;
    }
    .news-card:hover { 
        transform: translateY(-4px); 
        box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.1); 
        border-color: #6366f1;
    }

    /* TYPOGRAPHY */
    .news-card-content { padding: 16px; }
    .card-title a { 
        color: #000000 !important; 
        font-weight: 800; 
        font-size: 0.80rem !important; 
        line-height: 1.35; 
        text-decoration: none;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-title a:hover { color: #4338ca !important; }
    
    .card-desc { 
        font-size: 0.82rem !important; 
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
    
    .column-header { 
        padding: 0 0 10px 0;
        margin-bottom: 15px; 
        border-bottom: 2px solid #000;
        position: sticky;
        top: 0;
        background: white;
        z-index: 10;
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

    /* V38.0 Category Chips */
    .nav-chip {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        text-decoration: none;
        white-space: nowrap;
        transition: all 0.25s;
        cursor: pointer;
        margin-right: 10px;
        margin-bottom: 10px;
        color: #ffffff; /* Default text color for chips */
        border: 1px solid transparent; /* Default border */
    }

    .nav-chip.active {
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }

    .nav-chip:hover {
        opacity: 0.85;
        transform: translateY(-2px);
    }

    .category-spor { border-color: #86efac !important; }
    .category-ekonomi { border-color: #fde047 !important; }
    .category-teknoloji { border-color: #93c5fd !important; }
    .category-siyaset { border-color: #fca5a5 !important; }
    .category-dunya { border-color: #d6d3d1 !important; }
    .category-magazin { border-color: #fdba74 !important; }
    .category-muzik { border-color: #c4b5fd !important; }
    .category-home { border-color: #1e3a8a !important; }
    .category-turkiye { border-color: #fca5a5 !important; }
    .category-eglence { border-color: #fdba74 !important; }

    /* V38.4 Active State Styling */
    .nav-chip.active {
        border-width: 3px !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.06) !important;
        transform: translateY(-2px);
    }

    /* V38.4 Inline Expansion Styling */
    .inline-detail {
        grid-column: 1 / -1; 
        background: #ffffff;
        border-radius: 12px;
        padding: 5px;
        margin: 5px 0 25px 0;
        border: 1px solid #f8fafc;
        animation: slideDown 0.3s ease-out;
    }

    .inline-detail-mini {
        background: #ffffff;
        border-radius: 12px;
        padding: 0px;
        margin: 5px 0 15px 0;
        border: none;
        animation: slideDown 0.3s ease-out;
    }

    /* V38.8 5+2 SCROLLABLE NAV */
    .nav-tabs-wrapper {
        padding: 20px 25px !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        gap: 12px !important;
        margin-left: -1rem;
        margin-right: -1rem;
    }
    .nav-tabs-wrapper::-webkit-scrollbar { display: none; }
    
    .nav-chip {
        flex: 0 0 calc(20% - 10px) !important; /* Forces 5 visible items (20% - gap) */
        min-width: 130px;
        text-align: center;
        color: #000000 !important;
        background: #ffffff !important;
        border: 2px solid #e2e8f0;
        margin-right: 0 !important;
        padding: 10px 5px !important;
        font-size: 0.8rem !important;
    }

    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def render_twitter_embed(tweet_url):
    """Renders a live Twitter embed using components.html."""
    if not tweet_url or tweet_url in ["#", "None", ""]:
        st.info("💡 Bu haberin detaylı tweeti şu an yüklenemiyor veya kaynak silinmiş olabilir.")
        return

    embed_code = f"""
    <div style="display: flex; justify-content: center; width: 100%; border-radius: 12px; background: #ffffff; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <div style="width: 550px; max-width: 100%;">
            <blockquote class="twitter-tweet" data-theme="light">
                <a href="{tweet_url}"></a>
            </blockquote>
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        </div>
    </div>
    """
    components.html(embed_code, height=650)

def get_card_html(row, current_page_slug="home"):
    """Generates standardized HTML for a news card with URL sanitization."""
    content_raw = str(row.get('content', '')).replace("\n", " ")
    
    # V38.7 - Robust URL cleaning (Catches fragments like t.co, https://t, co/...)
    # 1. Standard URLs
    # 2. Fragmented t.co links (t.co/XYZ, co/XYZ)
    # 3. Cut-off https://t
    url_pattern = r'(https?://\S+|t\.co/\S+|co/\S+|https?://t\b)'
    clean_content = re.sub(url_pattern, '', content_raw).strip()
    
    if not clean_content: clean_content = content_raw
    
    # Robust Title/Desc Split using Regex (Avoiding dots in URLs)
    sentences = re.split(r'\.\s+', clean_content)
    
    if len(sentences) > 0 and len(sentences[0]) > 10:
        news_title = sentences[0].strip()[:100]
        news_desc = ". ".join(sentences[1:]).strip()[:120]
    else:
        news_title = clean_content[:100]
        news_desc = clean_content[100:200]
    
    if len(clean_content) > len(news_title): news_title += "..."
    if len(news_desc) > 0 and len(clean_content) > (len(news_title) + 5): news_desc += "..."
    
    # Escape for HTML safety
    news_title = html.escape(news_title)
    news_desc = html.escape(news_desc)
    author_name = html.escape(str(row.get('author') or 'ANONYMOUS')).upper()
    processed_at = html.escape(str(row.get('processed_at', '00:00')))
    tweet_url = row.get('tweet_url', '#')
    media_url = row.get('media_url')
    
    cat_val = row.get('category', 'HABER')
    cat_class = f"cat-{cat_val.lower().replace('ü', 'u').replace('ö', 'o').replace('ı', 'i').replace('ş', 's').replace('ç', 'c')}"

    media_html = f'<div style="width:100%; height:160px; overflow:hidden;"><img src="{media_url}" style="width:100%; height:100%; object-fit:cover;"></div>' if media_url else ""
    
    # V38.7 - FIXED: Removed inner <a> to prevent nested links. 
    # The entire card is wrapped in the expansion link already.
    title_html = f'<div style="color: #000000; font-weight: 800; font-size: 0.80rem; line-height: 1.35;">{news_title}</div>'
    
    # expansion routing bridge link - V38.7
    expand_url = f"/?page={current_page_slug}&expand={tweet_url}"
    
    return f'<a href="{expand_url}" target="_self" style="text-decoration:none; color:inherit; display:block;"><div class="news-card {cat_class}">{media_html}<div class="news-card-content"><div class="card-title">{title_html}</div><div class="card-desc">{news_desc}</div><div class="card-meta"><span>{author_name}</span><div class="sparkline"></div><span>{processed_at}</span></div></div></div></a>'

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
# APP LOGIC & ROUTING
# -----------------------------------------------------------------------------
# V38.5 - Internal Category Mapping (DB Name -> UI Label -> Slug)
category_config = [
    {"db": "Türkiye", "name": "Siyaset", "label": "Siyaset", "slug": "siyaset"},
    {"db": "Ekonomi", "name": "Ekonomi", "label": "Ekonomi", "slug": "ekonomi"},
    {"db": "Teknoloji", "name": "Teknoloji", "label": "Teknoloji", "slug": "teknoloji"},
    {"db": "Spor", "name": "Spor", "label": "Spor", "slug": "spor"},
    {"db": "Dünya", "name": "Dünya", "label": "Dünya", "slug": "dunya"},
    {"db": "Eğlence", "name": "Magazin", "label": "Magazin", "slug": "magazin"},
    {"db": "Müzik", "name": "Müzik", "label": "Müzik", "slug": "muzik"}
]

nav_items = [{"name": "Ana Sayfa", "label": "Ana Sayfa", "slug": "home"}] + [
    {"name": c["name"], "label": c["label"], "slug": c["slug"]} for c in category_config
]

# Query Parameter Routing Bridge
params = st.query_params
raw_slug = params.get("page", ["home"])[0] if isinstance(params.get("page"), list) else params.get("page", "home")
current_slug = slugify(raw_slug) # Force English slug
expand_url = params.get("expand")

# Determine Current Page Name & DB Category
current_item = next((item for item in nav_items if item["slug"] == current_slug or slugify(item["name"]) == current_slug), nav_items[0])
current_page = current_item["name"]
current_db_cat = next((c["db"] for c in category_config if c["name"] == current_page), None)

# Sidebar
with st.sidebar:
    st.markdown("### NUCLEUS X")
    st.markdown("---")
    
    # Nav Buttons
    for item in nav_items:
        is_active = current_page == item["name"]
        
        # High contrast Luxury state
        if is_active:
            st.markdown(f'''<style>div[data-testid="stSidebar"] div.stButton > button[key="nav_{item['name']}"] {{ background: #1e3a8a !important; color: #ffffff !important; font-weight: 800 !important; border: none !important; }}</style>''', unsafe_allow_html=True)
        else:
            st.markdown(f'''<style>div[data-testid="stSidebar"] div.stButton > button[key="nav_{item['name']}"] {{ background: #ffffff !important; color: #1e1e1e !important; font-weight: 600 !important; border-bottom: 1px solid #f1f5f9 !important; border-radius: 0 !important; text-align: left !important; }}</style>''', unsafe_allow_html=True)
        
        if st.button(item['label'], key=f"nav_{item['name']}", use_container_width=True):
            st.query_params["page"] = item["slug"]
            st.query_params.pop("expand", None) # Clear expand param
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
        <div class="logo-text">NUCLEUS<b>X</b> AI <small style="font-weight:400; font-size:0.6rem; opacity:0.6;">v38.6 Luxury</small></div>
""", unsafe_allow_html=True)

df = load_data()

# V38.8 - 5+2 DYNAMIC NAV TABS (Direct HTML for Scroll Support)
nav_html = '<div class="nav-tabs-wrapper">'
for item in nav_items:
    active_class = "active" if current_page == item["name"] else ""
    cat_class = f"category-{item['slug']}"
    nav_html += f'<a href="/?page={item["slug"]}" target="_self" class="nav-chip {cat_class} {active_class}">{item["label"]}</a>'
nav_html += '</div>'
st.markdown(nav_html, unsafe_allow_html=True)

# FOCUS VIEW REMOVED FROM TOP (V38.1)

selected_tag = st.session_state.get('selected_tag') # Keep selected_tag in session_state for now

if selected_tag:
    # Tag View
    st.markdown(f"### #{selected_tag} Gelişmeleri")
    tag_df = df[df['topic_tag'] == selected_tag]
    if not tag_df.empty:
        t_cols = st.columns(3)
        for idx, row in tag_df.iterrows():
            with t_cols[idx % 3]:
                st.markdown(get_card_html(row, current_page_slug=current_slug), unsafe_allow_html=True)
    if st.button("Geri Dön"):
        st.session_state.selected_tag = None
        st.rerun()
    st.stop()

if current_page != "Ana Sayfa":
    # Category Detail View - V33.0 3-COLUMN GRID
    cat_label = current_item["label"]
    st.markdown(f'<div style="padding: 20px 0; border-bottom: 2px solid #f1f5f9; margin-bottom: 30px;"><h2 style="font-weight:800; color:#1e3a8a;">{cat_label}</h2></div>', unsafe_allow_html=True)
    
    # Filter by DB Category mapping
    cat_df = df[df['category'] == current_db_cat].head(60)
    if not cat_df.empty:
        # 3-column grid as requested (3erli yan yana)
        grid = st.columns(3)
        for idx, row in cat_df.iterrows():
            with grid[idx % 3]:
                 st.markdown(get_card_html(row, current_page_slug=current_slug), unsafe_allow_html=True)
                 
                 # Inline Expansion for Categories
                 if expand_url and row.get('tweet_url') == expand_url:
                     st.markdown('<div class="inline-detail">', unsafe_allow_html=True)
                     render_twitter_embed(expand_url)
                     st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Bu kategoride henüz haber yok.")
    
    if st.button("← Ana Sayfaya Dön"):
        st.query_params["page"] = "home" # Set to home slug
        st.query_params.pop("expand", None)
        st.rerun()
    st.stop()

# Dashboard View
if current_page == "Ana Sayfa": # Changed from "Dashboard" to "Ana Sayfa"
    # Trending Pills
    if not df.empty:
        pop_tags = df[~df['topic_tag'].isin(["#HABER", "#GUNDEM", "#DETAY"])]['topic_tag'].value_counts().head(7).index.tolist()
        if pop_tags:
            pill_cols = st.columns(len(pop_tags))
            for i, pt in enumerate(pop_tags):
                if pill_cols[i].button(pt, key=f"p_{pt}", use_container_width=True):
                    st.session_state.selected_tag = pt
                    st.rerun()

    # Multi Column Feed - V38.3 Definitive
    visible_db_cats = [c["db"] for c in category_config if not df[df['category'] == c["db"]].empty]
    
    if visible_db_cats:
        # Use a single container for the horizontal scroll
        st.markdown('<div class="dashboard-wrapper">', unsafe_allow_html=True)
        
        # Determine column structure
        num_cats = len(visible_db_cats)
        dashboard_cols = st.columns(num_cats)
        
        for i, db_cat in enumerate(visible_db_cats):
            with dashboard_cols[i]:
                st.markdown(f'<div class="category-column">', unsafe_allow_html=True)
                
                # Get display label and slug for the category
                config = next(c for c in category_config if c["db"] == db_cat)
                cat_label = config["label"]
                cat_slug = config["slug"]
                
                st.markdown(f'<div class="column-header"><h3>{cat_label}</h3></div>', unsafe_allow_html=True)
                
                cat_df = df[df['category'] == db_cat].head(15)
                topics = cat_df.groupby('topic_tag')
                
                for t, group in topics:
                    tweet = group.iloc[0]
                    # Individual markdown calls are safer and prevent raw HTML leaks
                    st.markdown(get_card_html(tweet, current_page_slug=current_slug), unsafe_allow_html=True)
                    
                    # Inline Expansion in Dashboard
                    if expand_url and tweet.get('tweet_url') == expand_url:
                        st.markdown('<div class="inline-detail-mini">', unsafe_allow_html=True)
                        render_twitter_embed(expand_url)
                        st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Henüz haber verisi bulunmuyor. Lütfen yönetici panelinden tarama yapın.")

st.sidebar.markdown("---")
st.sidebar.caption("NucleusX V38.6 Luxury - Developed by Antigravity AI")
