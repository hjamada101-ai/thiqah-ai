import re
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from google import genai
from google.genai import types
import markdown
--- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(page_title="ثقة AI | حماية المتاجر الإلكترونية", page_icon="🛡️", layout="centered")
--- 2. التصميم الجمالي (UI/UX) CSS Injection ---
st.markdown("""
<style>
    /* استدعاء خط "تجوال" الفاخر مطابق للصورة المرفقة */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

    /* إخفاء واجهة Streamlit الافتراضية */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* تنسيق الخلفية والخط الأساسي */
    body, .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', sans-serif !important;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

    /* حقل إدخال الرابط */
    .stTextInput > div > div > input {
        text-align: left !important;
        direction: ltr !important;
        border-radius: 50px !important;
        border: 2px solid #CBD5E1 !important;
        padding: 16px 24px !important;
        font-size: 16px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        background: white !important;
        font-family: 'Tajawal', sans-serif !important;
    }

    /* زر الفحص الرئيسي */
    .stButton>button {
        background: linear-gradient(90deg, #10B981, #059669) !important;
        color: white !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 1.2rem !important;
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

    /* كروت الميزات */
    .modern-card {
        background: white;
        border-radius: 20px;
        padding: 25px 15px;
        text-align: center;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        height: 100%;
    }
    .modern-card-icon { font-size: 2.5rem; margin-bottom: 10px; }
    .modern-card-title { color: #1e293b; font-weight: 700; font-size: 1.1rem; margin-bottom: 8px; }
    .modern-card-text { color: #64748b; font-size: 0.9rem; line-height: 1.6; }

    /* تنسيق صندوق التقرير داخل الموقع (RTL دقيق) */
    .report-ui-box {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
        background: white;
        padding: 40px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        color: #1e293b;
        line-height: 1.9;
        font-size: 16px;
    }
    .report-ui-box h1, .report-ui-box h2, .report-ui-box h3 { color: #1e3a8a; font-weight: 700; margin-top: 25px; margin-bottom: 15px;}
    .report-ui-box table { width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 15px; }
    .report-ui-box th, .report-ui-box td { border: 1px solid #cbd5e1; padding: 14px; text-align: right; }
    .report-ui-box th { background-color: #f8fafc; color: #0f172a; font-weight: 700; }
    .report-ui-box strong { color: #0f172a; }
    .report-ui-box li { margin-bottom: 10px; }

    /* زر الدفع الفاخر */
    .premium-btn {
        display: block;
        text-align: center;
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        color: white !important;
        padding: 18px 30px;
        font-family: 'Tajawal', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        border-radius: 16px;
        text-decoration: none;
        margin-top: 20px;
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
    }
""", unsafe_allow_html=True)
--- 3. دوال المعالجة والذكاء الاصطناعي ---
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
found_links = re.findall(r'[([^]]+)]((https?://[^)]+))', main_content)
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
تجنب المقدمات الطويلة، ابدأ التقرير بعنوان رئيسي.
القسم الأخير سمه "الحلول والنصوص الجاهزة" واكتب فيه النصوص القانونية.
"""
prompt = f"افحص بيانات المتجر التالي وأصدر التقرير المنسق:\n\n{store_data}"
    for model_name in get_available_models(client):
        try:
            status_box.info(f"⏳ جاري التدقيق القانوني الشامل والمراجعة...")
            response = client.models.generate_content(
                model=model_name, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1)
            )
            if response.text: return response.text
        except: continue
    return "API_ERROR: النظام مزدحم حالياً، يرجى المحاولة بعد دقيقة."

def generate_export_html(markdown_text):
"""توليد ملف HTML فاخر جاهز للطباعة كـ PDF أو للفتح في Word"""
html_content = markdown.markdown(markdown_text, extensions=['tables'])
return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>تقرير الامتثال - منصة ثقة AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Tajawal', sans-serif;
            background-color: #ffffff;
            color: #1e293b;
            padding: 40px;
            line-height: 2;
            max-width: 900px;
            margin: auto;
            font-size: 16px;
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 3px solid #e2e8f0;
            margin-bottom: 40px;
        }}
        .header h1 {{ color: #1e3a8a; font-size: 32px; font-weight: 800; margin-bottom: 5px; }}
        .header p {{ color: #64748b; font-size: 16px; margin-top: 0; }}
        h1, h2, h3 {{ color: #1e3a8a; font-weight: 700; margin-top: 35px; margin-bottom: 15px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        th, td {{ padding: 15px; border: 1px solid #cbd5e1; text-align: right; }}
        th {{ background-color: #f1f5f9; color: #0f172a; font-weight: 700; }}
        strong {{ color: #0f172a; font-weight: 700; }}
        li {{ margin-bottom: 10px; }}
        @media print {{
            body {{ padding: 0; background-color: white; }}
            .header {{ margin-top: 20px; }}
        }}
    </style>
</head>
<body onload="window.print()">
    <div class="header">
        <h1>🛡️ تقرير الفحص القانوني للمتجر</h1>
        <p>تم استخراج هذا التقرير آلياً عبر منصة ثِقَة AI لتقييم الامتثال لاشتراطات التجارة الإلكترونية</p>
    </div>
    <div class="content">
        {html_content}
    </div>
</body>
</html>"""
جلب المفتاح السري
try: SECRET_API_KEY = st.secrets["GEMINI_API_KEY"]
except: SECRET_API_KEY = ""
--- 4. الهيكل البصري للمنصة ---
st.markdown("""
<div style="text-align: center; padding: 1rem 0 3rem 0;">
    <h1 style="font-weight: 800; font-size: 3.5rem; color: #1E3A8A; margin-bottom: 0;">
        منصة ثِقَة AI 🛡️
    </h1>
    <p style="color: #64748B; font-size: 1.2rem; margin-top: 15px; font-weight: 500;">
        الدرع القانوني لمتجرك الإلكتروني. افحص امتثالك لاشتراطات وزارة التجارة في ثوانٍ.
    </p>
</div>
""", unsafe_allow_html=True)
cols = st.columns(3)
features = [
("🇸🇦", "موثوقية سعودية", "تحديث فوري ليتوافق مع اشتراطات التجارة والمركز السعودي للأعمال."),
("🤖", "ذكاء اصطناعي", "خوارزميات متطورة تقرأ سياساتك وروابط التوثيق بدقة 100%."),
("⚡", "حلول فورية", "نوفر لك نصوصاً قانونية جاهزة للنسخ لتصحيح وضع متجرك فوراً.")
]
for i, col in enumerate(cols):
col.markdown(f'<div class="modern-card"><div class="modern-card-icon">{features[i][0]}</div><div class="modern-card-title">{features[i][1]}</div><div class="modern-card-text">{features[i][2]}</div></div>', unsafe_allow_html=True)
st.write("<br><br>", unsafe_allow_html=True)
st.markdown("<h3 style='color: #1E293B; font-weight: 700; text-align: right; margin-bottom: 15px;'>🔍 أدخل رابط متجرك للفحص الفوري:</h3>", unsafe_allow_html=True)
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
                
                # 1. عرض التقرير داخل الموقع بخط التجوال وتنسيق RTL دقيق جداً
                html_report_ui = markdown.markdown(report, extensions=['tables'])
                st.markdown(f'<div class="report-ui-box">{html_report_ui}</div>', unsafe_allow_html=True)
                
                st.write("<br>", unsafe_allow_html=True)
                
                # 2. أزرار التحميل (Word و PDF)
                export_html = generate_export_html(report)
                
                st.markdown("### 📥 تحميل التقرير:")
                dl_col1, dl_col2 = st.columns(2)
                
                with dl_col1:
                    st.download_button(
                        label="📄 تحميل كـ ملف PDF (جاهز للطباعة)",
                        data=export_html,
                        file_name="Thiqah_Report.html",
                        mime="text/html",
                        use_container_width=True
                    )
                with dl_col2:
                    st.download_button(
                        label="📝 تحميل كـ ملف Word (قابل للتعديل)",
                        data=export_html,
                        file_name="Thiqah_Report.doc",
                        mime="application/msword",
                        use_container_width=True
                    )
                
                # 3. دعوة الشراء
                st.markdown("""
                <div style="background: rgba(59, 130, 246, 0.05); border: 2px dashed #3B82F6; border-radius: 16px; padding: 30px; text-align: center; margin-top: 30px;">
                    <h2 style="color: #1E3A8A; font-weight: 700; font-size: 1.6rem; margin-bottom: 10px;">💡 هل اكتشفت ثغرات في متجرك؟</h2>
                    <p style="color: #475569; font-size: 1.1rem; line-height: 1.6;">
                        لا تخاطر بالغرامات! احصل الآن على مساعدة فنية لتصحيح متجرك بالكامل.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f'<a href="https://wa.me/966500000000?text=أهلاً، أريد تأمين متجري وتصحيح الأخطاء. هذا رابط متجري: {store_url}" target="_blank" class="premium-btn">🔒 تأمين المتجر والحصول على الحلول (99 ريال)</a>', unsafe_allow_html=True)
