import re
import streamlit as st
import streamlit.components.v1 as components
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
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    body, .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', sans-serif !important;
        background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
    }
    
    .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

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
        font-family: 'Tajawal', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important;
    }

    .stButton>button {
        background: linear-gradient(90deg, #10B981, #059669) !important;
        color: white !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
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
        font-family: 'Tajawal', sans-serif !important;
    }
    .modern-card-text {
        color: #64748B;
        font-size: 0.9rem;
        line-height: 1.5;
        font-family: 'Tajawal', sans-serif !important;
    }

    .premium-btn {
        display: block;
        text-align: center;
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        color: white !important;
        padding: 18px 30px;
        font-family: 'Tajawal', sans-serif;
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
</style>
""", unsafe_allow_html=True)

# --- 3. دوال الخلفية (البحث والتحليل الدقيق) ---
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
    has_saudi_business = any(x in full_raw_text for x in ["منصة الأعمال", "eauthenticate", "ال সৌদি للأعمال"])
    
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
    **هام جداً:** استخدم وسوم HTML نقية فقط (بدون أي تنسيقات Markdown مثل ### أو **).
    ابدأ التقرير فوراً هكذا:
    <h2>تقرير فحص الامتثال</h2>
    <p>مقدمة قصيرة هنا...</p>
    ثم استخدم الجداول (<table>) لعرض الفحص، والقوائم (<ul><li>) للتفاصيل.
    """
    prompt = f"افحص بيانات المتجر التالي وأصدر التقرير بتنسيق HTML نقي:\n\n{store_data}"
    
    for model_name in get_available_models(client):
        try:
            status_box.info(f"⏳ جاري التدقيق القانوني الشامل بواسطة الذكاء الاصطناعي...")
            response = client.models.generate_content(
                model=model_name, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1)
            )
            if response.text:
                 # Clean up Markdown code blocks if AI added them
                 clean_html = response.text.replace("```html", "").replace("```", "").strip()
                 return clean_html
        except: continue
    return "API_ERROR: النظام مزدحم حالياً، يرجى المحاولة بعد دقيقة."

# جلب المفتاح السري
try: SECRET_API_KEY = st.secrets["GEMINI_API_KEY"]
except: SECRET_API_KEY = ""

# --- 4. الهيكل البصري للمنصة (UI Structure) ---

st.markdown("""
<div style="text-align: center; padding: 2rem 0 3rem 0;">
    <h1 style="font-weight: 800; font-size: 3.5rem; background: linear-gradient(90deg, #1E3A8A, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0; font-family: 'Tajawal', sans-serif;">
        منصة ثِقَة AI 🛡️
    </h1>
    <p style="color: #64748B; font-size: 1.3rem; margin-top: 10px; font-weight: 500; font-family: 'Tajawal', sans-serif;">
        الدرع القانوني لمتجرك الإلكتروني. افحص امتثالك لاشتراطات وزارة التجارة في ثوانٍ.
    </p>
</div>
""", unsafe_allow_html=True)

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

st.markdown("<h3 style='color: #1E293B; font-weight: 700; text-align: right; margin-bottom: 15px; font-family: \"Tajawal\", sans-serif;'>🔍 أدخل رابط متجرك للفحص الفوري:</h3>", unsafe_allow_html=True)

store_url = st.text_input("", placeholder="مثال: https://alhulafa.com", label_visibility="collapsed")

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
            status_placeholder.error("⚠️ تعذر الوصول للمتجر، تأكد من صحة الرابط.")
        else:
            report = analyze_smart(scraped_data, SECRET_API_KEY, status_placeholder)
            if report.startswith("API_ERROR:"):
                status_placeholder.error(f"⚠️ {report}")
            else:
                status_placeholder.empty()
                st.success("✅ اكتمل الفحص! إليك التقرير المبدئي:")
                
                # إعداد وعرض HTML النقي داخل الواجهة مع تنسيقات كاملة
                full_html_content = f"""
                <div dir="rtl" style="font-family: 'Tajawal', sans-serif; text-align: right; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); color: #334155; line-height: 1.8;">
                    <style>
                        h1, h2, h3 {{ color: #1E3A8A; font-family: 'Tajawal', sans-serif; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th, td {{ border: 1px solid #e2e8f0; padding: 12px; text-align: right; }}
                        th {{ background-color: #f1f5f9; color: #1e293b; font-weight: 700; }}
                    </style>
                    {report}
                </div>
                """
                components.html(full_html_content, height=800, scrolling=True)
                
                st.write("<br>", unsafe_allow_html=True)
                
                # HTML القابل للتحميل كـ PDF (جاهز للطباعة)
                html_export = f"""
                <!DOCTYPE html>
                <html lang="ar" dir="rtl">
                <head>
                    <meta charset="UTF-8">
                    <title>تقرير فحص الامتثال</title>
                    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
                    <style>
                        body {{ font-family: 'Tajawal', sans-serif; background-color: #f8f9fa; padding: 40px; color: #334155; line-height: 1.8; }}
                        .container {{ max-width: 800px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
                        h1, h2, h3 {{ color: #1E3A8A; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th, td {{ border: 1px solid #e2e8f0; padding: 12px; text-align: right; }}
                        th {{ background-color: #f1f5f9; color: #1e293b; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        {report}
                    </div>
                    <script>
                        // خيار إضافي: يفتح نافذة الطباعة تلقائياً عند فتح الملف
                        window.onload = function() {{ window.print(); }}
                    </script>
                </body>
                </html>
                """
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📄 تحميل التقرير (جاهز للطباعة كـ PDF)",
                        data=html_export,
                        file_name="تقرير_امتثال_المتجر.html",
                        mime="text/html",
                        use_container_width=True
                    )
                with col2:
                    st.download_button(
                        label="📝 تحميل كود التقرير",
                        data=report,
                        file_name="تقرير_امتثال_المتجر.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

                st.markdown("""
                <div style="background: rgba(59, 130, 246, 0.05); border: 2px dashed #3B82F6; border-radius: 16px; padding: 30px; text-align: center; margin-top: 20px;">
                    <h2 style="color: #1E3A8A; font-weight: 700; font-size: 1.8rem; margin-bottom: 10px; font-family: 'Tajawal', sans-serif;">💡 هل اكتشفت ثغرات في متجرك؟</h2>
                    <p style="color: #475569; font-size: 1.1rem; line-height: 1.6; margin-bottom: 20px; font-family: 'Tajawal', sans-serif;">
                        الغرامات المالية تبدأ من 10,000 ريال للإخلال باشتراطات وزارة التجارة.<br>
                        لا تخاطر! احصل الآن على <b>تقرير قانوني مفصل + كافة النصوص الجاهزة</b> للنسخ واللصق لتأمين متجرك بالكامل.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(
                    f'<a href="https://wa.me/966500000000?text=أهلاً، أريد تأمين متجري وتصحيح الأخطاء القانونية. هذا رابط متجري: {store_url}" target="_blank" class="premium-btn">'
                    '🔒 تأمين المتجر والحصول على الحلول (99 ريال)'
                    '</a>', 
                    unsafe_allow_html=True
                )
