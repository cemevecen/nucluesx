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

# Premium CSS - Glassmorphism ve Modern Tasarım
st.markdown("""
    <style>
    .main {
        background-color: #ffffff !important;
        padding: 0;
    }
    .stApp {
        background-color: #f8fafc !important;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important;
    }
    .column-header {
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 10px;
        border-bottom: 3px solid #2563eb;
        margin-bottom: 20px;
        text-align: center;
        background: #ffffff !important;
        border-radius: 12px;
        color: #1e293b;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .news-card {
        background: #ffffff !important;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .news-card:hover {
        transform: translateY(-5px);
        border: 1px solid #2563eb;
        background: #ffffff !important;
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
    
    /* YATAY SWIPE (Scrollbar Gizli, Özel Deneyim) */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        gap: 15px !important;
        padding-bottom: 20px !important;
        scrollbar-width: none;
        -ms-overflow-style: none;
        scroll-snap-type: x mandatory;
    }
    
    [data-testid="stHorizontalBlock"]::-webkit-scrollbar {
        display: none !important;
    }
    
    div[data-testid="column"] {
        flex: 0 0 19% !important; /* 5 tanesini sığdır, geri kalanı taşır */
        min-width: 280px !important;
        flex-shrink: 0 !important; /* Sıkışmayı engelle (Taşması için kritik) */
        scroll-snap-align: start;
    }

    @media (max-width: 1400px) {
        div[data-testid="column"] {
            flex: 0 0 24% !important; /* 4 tanesi sığar */
        }
    }
    
    @media (max-width: 1000px) {
        div[data-testid="column"] {
            flex: 0 0 45% !important; /* 2 tanesi sığar */
        }
    }

    h1, h2, h3, p {
        color: #0f172a !important;
    }
    
    /* Sidebar Bembeyaz ve Yazılar Siyah (Premium) */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    /* TÜM sidebar elemanlarını tek tek lacivert/siyah yapalım */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background-color: #2563eb !important;
        color: white !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background-color: #2563eb !important;
        color: white !important;
        border: none;
    }
    /* Metin rengini özellikle beyaz isteyenler için (Eğer arka plan koyu kalsaydı) */
    /* Ancak kullanıcı bembeyaz sidebar istediği için siyah yapıyoruz */
    
    .topic-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .topic-hashtag {
        background: #2563eb;
        color: white !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 12px;
        margin-top: 10px;
    }
    .timeline-container {
        border-left: 2px solid #e2e8f0;
        padding-left: 15px;
        margin-left: 10px;
    }
    .timeline-item {
        position: relative;
        margin-bottom: 15px;
        padding-bottom: 5px;
    }
    .timeline-item::before {
        content: "";
        position: absolute;
        left: -21px;
        top: 5px;
        width: 10px;
        height: 10px;
        background: #2563eb;
        border-radius: 50%;
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

# Güvenlik ve Kotayı Korumak İçin: Admin Girişi (Basit Bir Önlem)
# Bu kısım botların veya rastgele kullanıcıların 'Scan' butonuna basıp kotanızı bitirmesini engeller.
with st.sidebar.expander("🔐 Yönetici Paneli"):
    admin_password = st.text_input("Tarama Şifresi", type="password")
    # Örnek şifre 'nucleus123' - Bunu Streamlit Secrets üzerinden yönetmek daha güvenlidir.
    ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "nucleus123")

st.sidebar.markdown("---")
st.sidebar.info("Bu panel, Twitter'dan çekilen ve AI tarafından kategorize edilen haberleri gösterir.")

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

# Ana Başlık
st.title("🎙️ NucleusX AI Newsroom")

# TREND HASHTAGLER (Kategori Tablarının Üzerinde)
GENERIC_TAG_LIST = ["#GELISME", "#GELİŞME", "#GUNDEM", "#GÜNDEM", "#HABER", "#DETAY", "#SONDAKIKA", "#SONDAKİKA"]
if not df.empty:
    # Trend konuları belirle (Örn: #FENERBAHCE)
    popular_tags = df[~df['topic_tag'].isin(GENERIC_TAG_LIST)]['topic_tag'].value_counts().head(10).index.tolist()
    
    if popular_tags:
        st.markdown('<div style="margin-bottom: 5px; color: #1e293b; font-weight: bold; font-size: 0.9rem;">🔥 GÜNCEL KONULAR</div>', unsafe_allow_html=True)
        # Etiketleri yan yana butonlar olarak diz
        tag_cols = st.columns(len(popular_tags) + 1)
        for idx, tag in enumerate(popular_tags):
            if tag_cols[idx].button(tag, key=f"trend_{tag}"):
                st.session_state.selected_tag = tag
                st.rerun()
        if st.session_state.selected_tag:
            if tag_cols[-1].button("❌ Filtreyi Kaldır", on_click=clear_tag):
                st.rerun()

st.markdown("---")

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
                
                # SADECE İLK (EN KALİTELİ) HABERİ GÖSTER
                main_news = group.iloc[0]
                clickable_main = make_clickable(main_news['content'])
                media_html = f'<img src="{main_news["media_url"]}" style="width:100%; border-radius:12px; margin-bottom:12px; object-fit:cover; height:180px; background:#f1f5f9;">' if main_news.get('media_url') else ""
                
                # Jenerik olmayan etiketler için "Grup" vurgusu yap
                if tag not in GENERIC_TAGS and len(group) > 1:
                    column_html += f"""
                        <div class="topic-hashtag" style="cursor:pointer; background:#2563eb;">{tag}</div>
                        <div class="topic-card">
                            {media_html}
                            <div class="tweet-content"><b>{main_news['author']}</b>: {clickable_main}</div>
                            <div style="border-top:1px solid #eee; margin-top:8px; padding-top:5px;">
                                <small style="color:#2563eb; font-weight:bold;">✨ {len(group)} farklı kaynak bu olayı geçti.</small>
                            </div>
                        </div>
                    """
                else:
                    display_tag = tag if tag in GENERIC_TAGS else tag
                    column_html += f"""
                        <div class="topic-hashtag" style="background:#64748b;">{display_tag}</div>
                        <div class="news-card">
                            {media_html}
                            <div class="tweet-content"><b>{main_news['author']}</b>: {clickable_main}</div>
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
