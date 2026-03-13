import streamlit as st # type: ignore
import re
import pandas as pd # type: ignore
import time
import html
import urllib.parse
from database import init_db, get_db_connection # type: ignore
from categorize_engine import run_categorization_process # type: ignore
import streamlit.components.v1 as components # type: ignore

# -----------------------------------------------------------------------------
# GLOBAL CONFIG & INITIALIZATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NucleusX AI V45.4 LUXURY",
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
GLOBAL_CSS = """
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
        box-sizing: border-box;
    }
    body { background: transparent !important; margin: 0; padding: 0; }
    .stApp { background-color: #ffffff !important; }
    .top-nav {
        display: flex; justify-content: space-between; align-items: center;
        padding: 15px 0; background: #ffffff !important; border-bottom: 1px solid #eff3f4;
        margin-top: -10px; margin-bottom: 25px;
    }
    .logo-text { font-weight: 800; font-size: 1.4rem; color: #0f1419; letter-spacing: -0.5px; }
    .logo-text b { color: #1d9bf0; }
    .dashboard-wrapper {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        gap: 15px !important;
        padding: 5px 0 20px 0 !important;
        width: 100% !important;
        scroll-behavior: smooth;
        scrollbar-width: thin;
        -webkit-overflow-scrolling: touch;
    }
    .category-column {
        flex: 0 0 19% !important;
        min-width: 280px !important;
        display: flex;
        flex-direction: column;
        gap: 0px !important;
        border-right: 1px solid #eff3f4;
    }
    .category-column .nav-chip, .nav-tabs-wrapper .nav-chip {
        display: block !important;
        background: #ffffff !important;
        color: #0f1419 !important;
        border: 1px solid #eff3f4 !important;
        border-radius: 24px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        text-align: center;
        text-decoration: none !important;
        margin: 12px 16px !important;
        transition: all 0.2s ease;
    }
    .nav-tabs-wrapper .nav-chip { margin: 0 !important; }
    .nav-chip:hover { background: #f7f9f9 !important; }
    .nav-chip.active { border-width: 3px !important; }
    .news-card {
        background: #ffffff !important;
        border: none !important;
        border-bottom: 1px solid #eff3f4 !important;
        border-left: 3px solid #6366f1 !important;
        border-radius: 0px !important;
        padding: 12px 16px !important;
        box-shadow: none !important;
        transition: background 0.2s ease;
        overflow: hidden;
        cursor: pointer;
        position: relative;
    }
    .news-card:hover { background: #f7f9f9 !important; }
    .author-avatar-small {
        width: 36px !important;
        height: 36px !important;
        border-radius: 50% !important;
        flex-shrink: 0 !important;
        object-fit: cover;
        margin: 0 !important;
    }
    .author-avatar-large {
        width: 44px !important;
        height: 44px !important;
        border-radius: 50% !important;
        flex-shrink: 0 !important;
        object-fit: cover;
        margin: 0 !important;
    }
    .card-meta-header {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
        margin-bottom: 6px !important;
    }
    .author-info {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        min-width: 0 !important;
    }
    .author-name {
        color: #0f1419;
        font-weight: 700;
        font-size: 0.875rem !important;
        line-height: 1.2 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .author-handle {
        color: #536471;
        font-size: 0.8rem !important;
        line-height: 1.2 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .tweet-text {
        font-size: 0.95rem;
        color: #0f1419;
        line-height: 1.5;
        margin-top: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-media-dashboard {
        width: 100%;
        max-height: 240px;
        border-radius: 12px;
        object-fit: cover;
        margin-top: 12px;
        border: 1px solid #eff3f4;
    }
    .card-stats-row {
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #eff3f4;
        display: flex;
        justify-content: space-between;
        max-width: 90%;
    }
    .stat-item {
        color: #536471;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .expanded-panel {
        background: #ffffff !important;
        border-bottom: 1px solid #eff3f4 !important;
        padding: 16px !important;
        position: relative;
        animation: fadeIn 0.3s ease-out;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .expanded-text {
        font-size: 1.1rem !important;
        color: #0f1419 !important;
        line-height: 1.6 !important;
        margin: 12px 0;
        white-space: pre-wrap;
    }
    .expanded-media {
        width: 100%;
        max-height: 480px;
        border-radius: 16px;
        object-fit: cover;
        margin: 16px 0;
        border: 1px solid #eff3f4;
    }
    .expanded-metadata {
        padding: 12px 0;
        border-top: 1px solid #eff3f4;
        color: #536471;
        font-size: 0.875rem;
    }
    .expanded-action-bar {
        padding: 12px 0;
        border-top: 1px solid #eff3f4;
        border-bottom: 1px solid #eff3f4;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }
    .action-icon {
        color: #536471;
        font-size: 1.1rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: color 0.15s;
    }
    .action-reply:hover { color: #1d9bf0 !important; }
    .action-rt:hover { color: #00ba7c !important; }
    .action-like:hover { color: #f91880 !important; }
    .close-btn-x {
        position: absolute;
        top: 12px;
        right: 16px;
        color: #0f1419;
        font-size: 1.25rem;
        text-decoration: none !important;
        padding: 8px;
        border-radius: 50%;
        line-height: 1;
    }
    .close-btn-x:hover { background: rgba(15, 20, 25, 0.1); }
    .news-card.cat-turkiye { border-left-color: #fca5a5 !important; }
    .news-card.cat-ekonomi { border-left-color: #fde047 !important; }
    .news-card.cat-teknoloji { border-left-color: #93c5fd !important; }
    .news-card.cat-spor { border-left-color: #86efac !important; }
    .news-card.cat-dunya { border-left-color: #d6d3d1 !important; }
    .news-card.cat-eglence { border-left-color: #fdba74 !important; }
    .news-card.cat-muzik { border-left-color: #c4b5fd !important; }
    @media (max-width: 991px) {
        .category-column { flex: 0 0 85vw !important; min-width: 85vw !important; }
    }
"""

st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def render_twitter_embed(tweet_url, dark=True):
    if not tweet_url or str(tweet_url) in ["#", "None", ""]:
        st.info("Bu tweete ait içerik yüklenemiyor.")
        return
    theme = "dark" if dark else "light"
    embed_code = f"""
    <div style="display:flex; justify-content:center; padding:20px 0;">
        <blockquote class="twitter-tweet" 
                    data-theme="{theme}" 
                    data-conversation="none" 
                    style="width:100%; max-width:550px;">
            <a href="{tweet_url}"></a>
        </blockquote>
        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    </div>
    """
    components.html(embed_code, height=700, scrolling=True)

def get_expanded_panel_html(row, current_page_slug="home"):
    """Generates X-style detail view for expanded news cards."""
    content_raw = str(row.get('content', '')).strip()
    media_url = row.get('media_url')
    author_name = html.escape(str(row.get('author') or 'ANONYMOUS'))
    author_image = row.get('author_image') or 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'
    processed_at = row.get('processed_at', '00:00')
    tweet_url = row.get('tweet_url', '#')
    handle = f"@{slugify(author_name)}"
    
    close_url = f"/?page={current_page_slug}"
    has_video = row.get('has_video', False)
    tweet_url = row.get('tweet_url', '#')

    if has_video and tweet_url and tweet_url != '#':
        # Twitter'ın kendi embed sistemi — video otomatik yüklenir
        media_html = f"""
        <div style="display:flex; justify-content:center; margin:16px 0;">
            <blockquote class="twitter-tweet" data-theme="dark" 
                        data-conversation="none" 
                        style="width:100%; max-width:550px;">
                <a href="{tweet_url}"></a>
            </blockquote>
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        </div>
        """
    elif media_url:
        media_html = f'<img src="{media_url}" class="expanded-media">'
    else:
        media_html = ""
    
    # Twitter Detail Layout V44.0
    html_out = f"""
    <div class="expanded-panel">
        <a href="{close_url}" target="_self" class="close-btn-x">✕</a>
        <div style="display:flex; flex-direction:row; align-items:center; gap:10px; margin-bottom:6px;">
            <img src="{author_image}" class="author-avatar-large">
            <div style="display:flex; flex-direction:column; justify-content:center; min-width:0;">
                <span class="author-name" style="font-size:0.95rem !important;">{author_name}</span>
                <span class="author-handle" style="font-size:0.85rem !important;">{handle}</span>
            </div>
        </div>
        <div class="expanded-text">{content_raw}</div>
        {media_html}
        <div class="expanded-metadata">
            {processed_at} · <span style="font-weight:700; color:#0f1419;">1.2B</span> Görüntülenme
        </div>
        <div class="expanded-action-bar">
            <div class="action-icon action-reply">💬 <span style="font-size:0.85rem">12</span></div>
            <div class="action-icon action-rt">🔁 <span style="font-size:0.85rem">45</span></div>
            <div class="action-icon action-like">❤️ <span style="font-size:0.85rem">156</span></div>
            <div class="action-icon action-share">🔖</div>
            <div class="action-icon action-share">📤</div>
        </div>
    </div>
    """
    return html_out.replace('\n', ' ')

def get_card_html(row, current_page_slug="home"):
    """Generates standardized HTML for a news card with onclick interaction V44.0."""
    content_raw = str(row.get('content', '')).replace("\n", " ")
    
    # V38.7 - Robust URL cleaning
    url_pattern = r'(https?://\S+|t\.co/\S+|co/\S+|https?://t\b)'
    clean_content = re.sub(url_pattern, '', content_raw).strip()
    if not clean_content: clean_content = content_raw
    
    # Title/Desc Split
    news_title = str(clean_content)
    news_desc = ""
    
    sentences = re.split(r'\.\s+', str(clean_content))
    if len(sentences) > 0:
        first_sentence = str(sentences[0]).strip()
        if len(first_sentence) > 10:
            news_title = first_sentence[0:100] # type: ignore
            news_desc = ". ".join(sentences[1:]).strip()[0:120] # type: ignore
        else:
            news_title = str(clean_content)[0:100] # type: ignore
            news_desc = str(clean_content)[100:200] # type: ignore
    
    if len(str(clean_content)) > len(str(news_title)): 
        news_title = f"{news_title}..."
    if len(str(news_desc)) > 0 and len(str(clean_content)) > (len(str(news_title)) + 5): 
        news_desc = f"{news_desc}..."
    
    # Escape for HTML safety
    news_title = html.escape(news_title)
    news_desc = html.escape(news_desc)
    author_name = html.escape(str(row.get('author') or 'ANONYMOUS'))
    processed_at = html.escape(str(row.get('processed_at', '00:00')))
    tweet_url = row.get('tweet_url', '#')
    media_url = row.get('media_url')
    author_image = row.get('author_image') or 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'
    
    cat_val = row.get('category', 'HABER')
    cat_mapping = cat_val.lower().replace('ü', 'u').replace('ö', 'o').replace('ı', 'i').replace('ş', 's').replace('ç', 'c')
    if cat_mapping == "turkiye": cat_mapping = "turkiye" # Specific fix for Türkiye -> turkiye
    cat_class = f"cat-{cat_mapping}"

    handle = f"@{slugify(author_name)}"
    # Graphics & Stats logic
    reply_count   = int(row.get('reply_count',   0) or 0)
    retweet_count = int(row.get('retweet_count', 0) or 0)
    like_count    = int(row.get('like_count',    0) or 0)

    def fmt(n):
        if n >= 1000000: return f"{n/1000000:.1f}M"
        if n >= 1000:    return f"{n/1000:.1f}B"
        return str(n)

    # Media HTML logic for Dashboard (Thumbnail + Inline Play Button JS)
    has_video = row.get('has_video', False)
    card_id = abs(hash(str(tweet_url))) % 999999
    safe_tweet_url = str(tweet_url) if tweet_url else "#"
    
    if has_video and media_url:
        media_html = f"""
        <div style="position:relative; width:100%; border-radius:12px; overflow:hidden; border:1px solid #eff3f4; margin-top:12px;">
            <img src="{media_url}" style="width:100%; max-height:240px; object-fit:cover; display:block;">
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:48px; height:48px; background:rgba(29,155,240,0.9); border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 12px rgba(0,0,0,0.2);">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>
            </div>
            <div style="position:absolute; bottom:8px; right:8px; background:rgba(0,0,0,0.7); color:white; font-size:0.7rem; padding:2px 6px; border-radius:4px; font-weight:700;">VIDEO</div>
        </div>
        """
    elif media_url:
        media_html = f'<img src="{media_url}" class="card-media-dashboard">'
    else:
        media_html = ""
    
    # Determine if this card IS expanded
    current_expanded = str(st.query_params.get("expand") or "")
    is_open = (current_expanded == str(tweet_url))
    
    # URL for onclick redirection
    encoded_url = urllib.parse.quote_plus(safe_tweet_url)
    target_url = f"/?page={current_page_slug}" if is_open else f"/?page={current_page_slug}&expand={encoded_url}"
    js_nav = f"window.parent.location.href = '{target_url}';"
    
    # Stats Row with real counts and formatted icons
    stats_html = f"""
    <div class="card-stats-row">
        <div class="stat-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#536471"><path d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 7.498 3.858 6.629 8.138-.064.315-.128.63-.192.95-.056.29-.114.58-.176.86-.077.34-.161.68-.248 1.02l1.26 1.26c.36.36.53.86.46 1.34l-.96 6.37c-.1.66-.77 1.06-1.4.84l-5.12-1.71c-.34-.11-.56-.43-.56-.79V18.5a.75.75 0 01-.75-.75v-3.5c0-.41.34-.75.75-.75h1.5c.34 0 .64.22.72.55l.29 1.17 3.45 1.15.72-4.77-1.63-1.63A.75.75 0 0119 9.25c0-.1.01-.2.03-.29.07-.29.14-.58.21-.87.06-.28.12-.55.18-.82.64-3.13-1.62-5.97-4.83-5.97H9.756C7.478 1.5 5.5 3.43 5.5 5.75c0 .62.14 1.22.41 1.77l-1.41.71A5.23 5.23 0 014 5.75C4 2.57 6.57 0 9.756 0h4.366C18.48 0 22 3.42 21.128 8H21.5a.75.75 0 010 1.5h-.96l-.03.13-.21.87-.18.82A2.25 2.25 0 0122 13.25v.5c0 .41-.34.75-.75.75h-.5a.75.75 0 010-1.5v-.5a.75.75 0 00-.75-.75H18.5a.75.75 0 000 1.5h.25v.5a.75.75 0 01-.75.75H17a.75.75 0 010-1.5h.25v-.5a2.25 2.25 0 00-2.25-2.25z"/></svg>
            {fmt(reply_count)}
        </div>
        <div class="stat-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#536471"><path d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2H13v2H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"/></svg>
            {fmt(retweet_count)}
        </div>
        <div class="stat-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#536471"><path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-1.243.07-2.349.78-2.91 1.91-.552 1.12-.633 2.78.479 4.82 1.074 1.97 3.257 4.27 7.129 6.61 3.87-2.34 6.052-4.64 7.126-6.61 1.111-2.04 1.03-3.7.477-4.82-.561-1.13-1.666-1.84-2.908-1.91z"/></svg>
            {fmt(like_count)}
        </div>
        <div class="stat-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#536471"><path d="M4 4.5C4 3.12 5.119 2 6.5 2h11C18.881 2 20 3.12 20 4.5v18.44l-8-5.71-8 5.71V4.5zM6.5 4c-.276 0-.5.22-.5.5v14.56l6-4.29 6 4.29V4.5c0-.28-.224-.5-.5-.5h-11z"/></svg>
        </div>
    </div>
    """
    
    # Return card wrapped in standard <a> for top-level navigation
    html_card = f"""
    <a href="{target_url}" target="_self" style="text-decoration:none; color:inherit; display:block;">
        <div class="news-card {cat_class}">
            <div class="card-meta-header">
                <img src="{author_image}" class="author-avatar-small">
                <div class="author-info">
                    <span class="author-name">{author_name}</span>
                    <span class="author-handle">{handle}</span>
                </div>
            </div>
            <div class="tweet-text">{news_title} {news_desc}</div>
            {media_html}
            {stats_html}
            <div style="display:flex; justify-content:flex-end; margin-top:4px;">
                <span class="timestamp" style="font-size:0.75rem;">{processed_at}</span>
            </div>
        </div>
    </a>
    """
    return html_card.replace('\n', ' ')

@st.cache_data(ttl=600)
def load_data():
    try:
        conn = get_db_connection()
        query = """
        SELECT author, username, content, category, topic_tag, processed_at, 
               media_url, tweet_url, author_image,
               COALESCE(has_video, FALSE)     as has_video,
               COALESCE(reply_count, 0)       as reply_count,
               COALESCE(retweet_count, 0)     as retweet_count,
               COALESCE(like_count, 0)        as like_count
        FROM tweets 
        WHERE processed_at > NOW() - INTERVAL '7 days' 
        ORDER BY processed_at DESC LIMIT 500
    """
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
raw_slug = params.get("page", "home")
if isinstance(raw_slug, list): raw_slug = raw_slug[0] 
current_slug = slugify(str(raw_slug)) # Force English slug
expand_url = str(params.get("expand") or "")
if isinstance(expand_url, list): expand_url = expand_url[0]

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

df = load_data()

# Combined Header & Nav Tabs - V39.7 (Unified Alignment)
header_html = f"""
    <div class="top-nav">
        <a href="/?page=home" target="_self" style="text-decoration: none; color: inherit;">
            <div class="logo-text">NUCLEUS<b>X</b></div>
        </a>
    </div>
"""

# Only show top chips bar if NOT on Ana Sayfa (On Ana Sayfa they are column headers)
if current_page != "Ana Sayfa":
    header_html += '<div class="nav-tabs-wrapper" style="padding: 5px 0 25px 0 !important; display: flex; gap: 12px; overflow-x: auto;">'
    for item in nav_items:
        if item["slug"] == "home": continue
        active_class = "active" if current_page == item["name"] else ""
        cat_class = f"category-{item['slug']}"
        header_html += f'<a href="/?page={item["slug"]}" target="_self" class="nav-chip {cat_class} {active_class}" style="flex:0 0 auto; min-width:140px;">{item["label"]}</a>'
    header_html += '</div>'

st.markdown(header_html, unsafe_allow_html=True)

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
        # Category view with inline expansion
        for idx, row in cat_df.iterrows():
            st.markdown(get_card_html(row, current_page_slug=current_slug), unsafe_allow_html=True)
            
            # Inline Expansion logic (V45.5 - Hybrid Model)
            if expand_url and row.get('tweet_url') == expand_url:
                has_video = row.get('has_video', False)
                if has_video:
                    render_twitter_embed(expand_url)
                else:
                    st.markdown(get_expanded_panel_html(row, current_page_slug=current_slug), unsafe_allow_html=True)
    else:
        st.info("Bu kategoride henüz haber yok.")
    
    if st.button("← Ana Sayfaya Dön"):
        st.query_params["page"] = "home" # Set to home slug
        st.query_params.pop("expand", None)
        st.rerun()
    st.stop()

# Dashboard View - V40.0 Unified Scroll with Raw HTML
if current_page == "Ana Sayfa":
    visible_db_cats = [c["db"] for c in category_config if not df[df['category'] == c["db"]].empty]
    
    if visible_db_cats:
        dashboard_html = '<div class="dashboard-wrapper">'
        
        for db_cat in visible_db_cats:
            config = next(c for c in category_config if c["db"] == db_cat)
            cat_slug = config["slug"]
            cat_label = config["label"]
            cat_class = f"category-{cat_slug}"
            
            # Start Category Column
            column_html = f'<div class="category-column">'
            
            # 1. Render Chip at the top of the column
            column_html += f'<a href="/?page={cat_slug}" target="_self" class="nav-chip {cat_class} active">{cat_label}</a>'
            
            # 2. Add News Cards (Top 30 news per category, no complex grouping for dashboard)
            cat_df = df[df['category'] == db_cat].head(30)
            
            for idx, tweet in cat_df.iterrows():
                card_html = get_card_html(tweet, current_page_slug=current_slug)
                column_html += card_html
                
                # 3. Handle Expansion (Inline Detail V43.0)
                if expand_url and tweet.get('tweet_url') == expand_url:
                    panel_html = get_expanded_panel_html(tweet, current_page_slug=current_slug)
                    column_html = f"{column_html}{panel_html}"
            column_html = f"{column_html}</div>" # End Category Column
            dashboard_html = f"{dashboard_html}{column_html}"
            
        dashboard_html = f"{dashboard_html}</div>" # End Dashboard Wrapper
        
        # Render the dashboard with st.markdown
        # This ensures standard <a> links work for page navigation
        st.markdown(dashboard_html, unsafe_allow_html=True)
    else:
        st.warning("Henüz haber verisi bulunmuyor. Lütfen yönetici panelinden tarama yapın.")

st.sidebar.markdown("---")
st.sidebar.caption("NucleusX v45.4 - Developed by ivicin")
