import re
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from google import genai
from google.genai import types

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(page_title="ثقة AI | حماية المتاجر الإلكترونية", page_icon="🛡️", layout="centered")

# --- 2. التصميم الجمالي (UI/UX) CSS Injection ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Alexandria:wght@300;400;600;700&display=swap');

    /* إخفاء واجهة Streamlit الافتراضية */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* تنسيق الخلفية والخط الأساسي */
    body, .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Alexandria', sans-serif !important;
        background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
    }
    
    /* توسيط المحتوى وإعطاء مساحة للتنفس */
    .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

    /* حقل إدخال الرابط (عصري ودائري) */
    .stTextInput > div > div > input {
        text-align: left !important;
        direction: ltr !important;
        border-radius: 50px !important;
        border: 2px solid #CBD5E1 !important;
        padding: 16px 24px !important;
        font-size: 16px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: all 0.3s ease;
        background: white !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important;
    }

    /* زر الفحص الرئيسي */
    .stButton>button {
        background: linear-gradient(90deg, #10B981, #059669) !important;
        color: white !important;
        font-family: 'Alexandria', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border-radius: 50px !important;
        padding: 12px 24px !important;
        width: 100% !important;
        border: none !important;
        box-shadow: 0 10px 20px -5px rgba(16, 185, 129, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 25px -5px rgba(16, 185, 129, 0.5) !important;
    }

    /* كروت الميزات (التأثير الزجاجي) */
    .modern-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 30px 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        height: 100%;
    }
    .modern-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.08);
        border-color: rgba(59, 130, 246, 0.3);
    }
    .modern-card-icon {
        font-size: 3rem;
        margin-bottom: 15px;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
    }
    .modern-card-title {
        color: #1E293B;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }
    .modern-card-text {
        color: #64748B;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* زر الدفع الجذاب (SaaS Style) */
    .premium-btn {
        display: block;
        text-align: center;
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        color: white !important;
        padding: 18px 30px;
        font-family: 'Alexandria', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        border-radius: 16px;
        text-decoration: none;
        margin-top: 30px;
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .premium-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(59, 130, 246, 0.5);
    }
    /* تأثير اللمعة للزر */
    .premium-btn::after {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 50%; height: 100%;
        background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0) 100%);
        transform: skewX(-20deg);
        animation: shine 3s infinite;
    }
    @keyframes shine {
        0% { left: -100%; }
        20% { left: 200%; }
        100% { left: 200%; }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. دوال الخلفية (البحث والتحليل الدقيق) - لم تتغير ---
def fetch_rendered_page(url):
    try:
        reader_url = f"https://r.jina.ai/{url}"
        headers = {'Accept': 'text/plain', 'X-Return-Format': 'markdown'}
        res = requests.get(reader_url, headers=headers, timeout=20)
        if res.status_code == 200 and len(res.text) > 200: return res.text
    except: pass
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except Exception as e: return f"ERROR: {str(e)}"

def extract_contact_and_policies(base_url):
    main_content = fetch_rendered_page(base_url)
    if main_content.startswith("ERROR:"): return main_content
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc.replace("www.", "")
    found_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', main_content)
    priority_keywords = ['تواصل', 'contact', 'شكاوى', 'استرجاع', 'استبدال', 'return', 'refund', 'شحن', 'توصيل', 'shipping', 'خصوصية', 'privacy', 'شروط', 'terms', 'سياسة']
    visited = set([base_url, base_url.rstrip('/')])
    subpages_content = ""
    sorted_links = sorted(found_links, key=lambda x: 0 if any(k in x[0].lower() for k in ['تواصل', 'contact']) else 1)
    
    for link_text, link_url in sorted_links:
        clean_url = link_url.split('#')[0].rstrip('/')
        if any(kw in link_text.lower() or kw in clean_url.lower() for kw in priority_keywords):
            if base_domain in urlparse(clean_url).netloc and clean_url not in visited:
                visited.add(clean_url)
                page_text = fetch_rendered_page(clean_url)
                if not page_text.startswith("ERROR:"): subpages_content += f"\n\n=== محتوى صفحة: {link_text} ===\n{page_text[:3500]}"
                if len(visited) >= 6: break

    header_and_footer = main_content[:3000] + "\n\n... [ذيل الصفحة] ...\n\n" + main_content[-5500:] if len(main_content) > 8500 else main_content
    full_raw_text = main_content + "\n" + subpages_content
    
    phones = set(re.findall(r'(?:\+966|00966|966|0)?5\d{8}|9200\d{5}|800\d{7}', full_raw_text))
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_raw_text))
    vat_numbers = set(re.findall(r'\b3\d{13}3\b', full_raw_text))
    cr_numbers = set(re.findall(r'\b(?:10|20|40|70)\d{8}\b', full_raw_text))
    has_saudi_business = any(x in full_raw_text for x in ["منصة الأعمال", "eauthenticate", "المركز السعودي للأعمال"])
    
    auto_extracted = (f"\n\n=== بيانات مرصودة آلياً ===\nالسجلات: {', '.join(cr_numbers)}\nالضريبي: {', '.join(vat_numbers)}\nالتوثيق: {has_saudi_business}\nواتساب/هاتف: {', '.join(phones)}\nإيميل: {', '.join(emails)}")
    return f"=== الصفحة الرئيسية ===\n{header_and_footer}\n{subpages_content}{auto_extracted}"

def get_available_models(client):
    try:
        models = [m.name.replace("models/", "") for m in client.models.list() if "gemini" in m.name and not any(x in m.name for x in ["image", "vision", "embedding", "aqa", "tts", "audio", "robotics"])]
        models.sort(key=lambda x: 1 if "lite" in x else (2 if "flash" in x else 3))
        return models if models else ["gemini-3.8-flash"]
    except: return ["gemini-3.8-flash"]

def analyze_smart(store_data, api_key, status_box):
    client = genai.Client(api_key=api_key.strip())
    system_instruction = """
    أنت مستشار قانوني سعودي. افحص المتجر بناءً على نظام التجارة الإلكترونية.
    ركز على: السجل/التوثيق، الرقم الضريبي، سياسة الاسترجاع (7 أيام)، الشحن (15 يوماً)، الخصوصية، بيانات التواصل.
    اكتب التقرير ليقرأه صاحب المتجر مباشرة، واجعله يبدو احترافياً.
    تجنب ذكر "بناءً على المعطيات"، ابدأ التقرير فوراً بعبارة ترحيبية احترافية مثل: "تقرير فحص الامتثال لمتجرك..."
    """
    prompt = f"افحص بيانات المتجر التالي وأصدر التقرير:\n\n{store_data}"
    
    for model_name in get_available_models(client):
        try:
            status_box.info(f"⏳ جاري التدقيق القانوني الشامل بواسطة الذكاء الاصطناعي...")
            response = client.models.generate_content(
                model=model_name, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1)
            )
            if response.text: return response.text
        except: continue
    return "API_ERROR: النظام مزدحم حالياً، يرجى المحاولة بعد دقيقة."

# جلب المفتاح السري
try: SECRET_API_KEY = st.secrets["GEMINI_API_KEY"]
except: SECRET_API_KEY = ""


# --- 4. الهيكل البصري للمنصة (UI Structure) ---

# قسم الترحيب (Hero Section)
st.markdown("""
<div style="text-align: center; padding: 2rem 0 3rem 0;">
    <h1 style="font-weight: 800; font-size: 3.5rem; background: linear-gradient(90deg, #1E3A8A, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0;">
        منصة ثِقَة AI 🛡️
    </h1>
    <p style="color: #64748B; font-size: 1.3rem; margin-top: 10px; font-weight: 400;">
        الدرع القانوني لمتجرك الإلكتروني. افحص امتثالك لاشتراطات وزارة التجارة في ثوانٍ.
    </p>
</div>
""", unsafe_allow_html=True)

# كروت المميزات
cols = st.columns(3)
features = [
    ("🇸🇦", "موثوقية سعودية", "تحديث فوري ليتوافق مع اشتراطات وزارة التجارة والمركز السعودي للأعمال."),
    ("🤖", "ذكاء اصطناعي", "خوارزميات متطورة تقرأ سياساتك، أرقامك، وروابط التوثيق بدقة 100%."),
    ("⚡", "حلول فورية", "نوفر لك نصوصاً قانونية جاهزة للنسخ لتصحيح وضع متجرك فوراً.")
]
for i, col in enumerate(cols):
    col.markdown(f"""
    <div class="modern-card">
        <div class="modern-card-icon">{features[i][0]}</div>
        <div class="modern-card-title">{features[i][1]}</div>
        <div class="modern-card-text">{features[i][2]}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("<br><br>", unsafe_allow_html=True)

# منطقة الإدخال والفحص
st.markdown("<h3 style='color: #1E293B; font-weight: 700; text-align: right; margin-bottom: 15px;'>🔍 أدخل رابط متجرك للفحص الفوري:</h3>", unsafe_allow_html=True)

store_url = st.text_input("", placeholder="مثال: https://alhulafa.com", label_visibility="collapsed")

if st.button("🚀 ابدأ الفحص المجاني الآن"):
    if not SECRET_API_
