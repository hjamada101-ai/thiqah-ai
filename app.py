import re
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from google import genai
from google.genai import types

# 1. إعدادات الصفحة (يجب أن تكون أول سطر)
st.set_page_config(page_title="ثقة AI | حماية المتاجر الإلكترونية", page_icon="🛡️", layout="centered")

# 2. تصميم CSS احترافي (إخفاء قوائم Streamlit وتجميل الواجهة)
st.markdown("""
<style>
    /* إخفاء القوائم العلوية والسفلية الخاصة بـ Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* تنسيق عام */
    body, .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', 'Segoe UI', Tahoma, sans-serif;
        background-color: #f8f9fa;
    }
    
    /* تنسيق العناوين */
    h1, h2, h3, p, div { text-align: right; }
    .main-title {
        color: #1E3A8A;
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center !important;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #4B5563;
        font-size: 1.2rem;
        text-align: center !important;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    
    /* تنسيق زر الفحص */
    .stButton>button {
        background-color: #10B981 !important; /* أخضر ثقة */
        color: white !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        width: 100% !important;
        border: none !important;
        transition: 0.3s;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover {
        background-color: #059669 !important;
        transform: translateY(-2px);
    }
    
    /* تنسيق صندوق الإدخال */
    .stTextInput > div > div > input {
        text-align: left !important;
        direction: ltr !important;
        border-radius: 8px;
        border: 2px solid #E5E7EB;
        padding: 12px;
        font-size: 16px;
    }
    
    /* تنسيق صندوق الميزات */
    .feature-box {
        text-align: center !important;
        padding: 20px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* زر الدفع المميز */
    .pay-button {
        display: block;
        text-align: center;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        color: white !important;
        padding: 15px 20px;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 10px;
        text-decoration: none;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

# دوال السحب والتحليل (نفس الدقة السابقة 100%)
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
    القسم الأخير سمه "الحلول والنصوص الجاهزة (باقة Premium)" واكتب فيه النصوص القانونية.
    """
    prompt = f"افحص بيانات المتجر التالي وأصدر التقرير:\n\n{store_data}"
    
    for model_name in get_available_models(client):
        try:
            status_box.info(f"⏳ جاري تدقيق السياسات عبر الذكاء الاصطناعي...")
            response = client.models.generate_content(
                model=model_name, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1)
            )
            if response.text: return response.text
        except: continue
    return "API_ERROR: النظام مزدحم حالياً، يرجى المحاولة بعد دقيقة."

# جلب المفتاح
try: SECRET_API_KEY = st.secrets["GEMINI_API_KEY"]
except: SECRET_API_KEY = ""


# --- واجهة المستخدم الاحترافية ---

st.markdown('<p class="main-title">منصة ثِقَة AI 🛡️</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">هل متجرك الإلكتروني محمي من غرامات وزارة التجارة؟ افحص امتثالك في 30 ثانية.</p>', unsafe_allow_html=True)

# مميزات المنصة (لزيادة الثقة)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="feature-box">🇸🇦<br><b>متوافق مع الأنظمة</b><br><small>وزارة التجارة والمركز السعودي للأعمال</small></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="feature-box">🤖<br><b>فحص دقيق جداً</b><br><small>بالذكاء الاصطناعي يقرأ كل سياسات متجرك</small></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="feature-box">⚡<br><b>حلول فورية</b><br><small>نصوص قانونية جاهزة للنسخ واللصق</small></div>', unsafe_allow_html=True)

st.write("---")

st.markdown("### 🔍 أدخل رابط متجرك لفحص مجاني للثغرات:")
store_url = st.text_input("", placeholder="مثال: https://alhulafa.com")

if st.button("🚀 ابدأ الفحص المجاني الآن"):
    if not SECRET_API_KEY:
        st.error("⚠️ عذراً، النظام في وضع الصيانة.")
    elif not store_url or not store_url.startswith("http"):
        st.warning("⚠️ يرجى إدخال رابط متجر صحيح يبدأ بـ https://")
    else:
        status_placeholder = st.empty()
        status_placeholder.info("🌐 جاري تحليل هيكل المتجر واستخراج السياسات القانونية...")
        scraped_data = extract_contact_and_policies(store_url.strip())
            
        if scraped_data.startswith("ERROR:"):
            status_placeholder.error("⚠️ تعذر الوصول للمتجر، تأكد من الرابط.")
        else:
            report = analyze_smart(scraped_data, SECRET_API_KEY, status_placeholder)
            if report.startswith("API_ERROR:"):
                status_placeholder.error(f"⚠️ {report}")
            else:
                status_placeholder.empty()
                st.success("✅ اكتمل الفحص! إليك تقرير متجرك المبدئي:")
                
                # عرض النتيجة داخل حاوية أنيقة
                with st.container(border=True):
                    st.markdown(report)
                
                st.write("---")
                st.markdown("### 💡 هل اكتشفت ثغرات في متجرك؟")
                st.markdown("لا تخاطر بالغرامات! احصل الآن على **ملف التقرير الكامل بصيغة PDF + جميع النصوص القانونية المخصصة لمتجرك** جاهزة للنسخ واللصق، بالإضافة إلى دعم فني لتصحيح أخطاء متجرك.")
                
                # زر الدفع الوهمي (ستربطه لاحقاً بـ Paylink أو واتسابك)
                st.markdown(
                    f'<a href="https://wa.me/966500000000?text=أهلاً، أريد شراء باقة تصحيح متجري: {store_url}" target="_blank" class="pay-button">'
                    '💳 احصل على الباقة المتكاملة بـ 99 ريال فقط'
                    '</a>', 
                    unsafe_allow_html=True
                )
