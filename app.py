import re
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from google import genai
from google.genai import types

st.set_page_config(page_title="ثقة AI | فاحص امتثال المتاجر السعودية", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    body, .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stTextInput > div > div > input { text-align: right; }
    h1, h2, h3, p, div { text-align: right; }
</style>
""", unsafe_allow_html=True)

def fetch_rendered_page(url):
    """جلب الصفحة بعد تشغيل JavaScript بالكامل عبر Jina Reader"""
    try:
        reader_url = f"https://r.jina.ai/{url}"
        headers = {'Accept': 'text/plain', 'X-Return-Format': 'markdown'}
        res = requests.get(reader_url, headers=headers, timeout=20)
        if res.status_code == 200 and len(res.text) > 200:
            return res.text
    except Exception:
        pass
    
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        return f"ERROR: {str(e)}"

def extract_contact_and_policies(base_url):
    main_content = fetch_rendered_page(base_url)
    if main_content.startswith("ERROR:"):
        return main_content

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc.replace("www.", "")
    
    found_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', main_content)
    
    priority_keywords = [
        'تواصل', 'اتصل', 'contact', 'شكاوى',
        'استرجاع', 'استبدال', 'return', 'refund',
        'شحن', 'توصيل', 'shipping', 'delivery',
        'خصوصية', 'privacy', 'شروط', 'terms', 'سياسة'
    ]
    
    visited = set([base_url, base_url.rstrip('/')])
    subpages_content = ""
    
    sorted_links = sorted(
        found_links,
        key=lambda x: 0 if any(k in x[0].lower() for k in ['تواصل', 'اتصل', 'contact']) else 1
    )
    
    for link_text, link_url in sorted_links:
        clean_url = link_url.split('#')[0].rstrip('/')
        if any(kw in link_text.lower() or kw in clean_url.lower() for kw in priority_keywords):
            if base_domain in urlparse(clean_url).netloc and clean_url not in visited:
                visited.add(clean_url)
                page_text = fetch_rendered_page(clean_url)
                if not page_text.startswith("ERROR:"):
                    subpages_content += f"\n\n=== محتوى صفحة: {link_text} ({clean_url}) ===\n{page_text[:3500]}"
                if len(visited) >= 7:
                    break

    # أخذ بداية الصفحة + نهاية الصفحة (لضمان عدم قص ذيل الصفحة Footer أبداً)
    if len(main_content) > 8500:
        header_and_footer = main_content[:3000] + "\n\n... [ذيل الصفحة والمعلومات القانونية في الأسفل] ...\n\n" + main_content[-5500:]
    else:
        header_and_footer = main_content

    full_raw_text = main_content + "\n" + subpages_content
    
    # استخراج آلي دقيق لجميع البيانات القانونية والتواصل من كامل الصفحة قبل أي قص
    phones = set(re.findall(r'(?:\+966|00966|966|0)?5\d{8}|9200\d{5}|800\d{7}', full_raw_text))
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_raw_text))
    vat_numbers = set(re.findall(r'\b3\d{13}3\b', full_raw_text)) # الرقم الضريبي السعودي 15 رقماً يبدأ وينتهي بـ 3
    cr_numbers = set(re.findall(r'\b(?:10|20|40|70)\d{8}\b', full_raw_text)) # السجل التجاري أو الرقم الموحد للمنشأة 10 أرقام
    has_saudi_business = "منصة الأعمال" in full_raw_text or "eauthenticate" in full_raw_text or "المركز السعودي للأعمال" in full_raw_text
    
    auto_extracted = (
        f"\n\n=== بيانات قانونية وتواصل تم رصدها آلياً بدقة 100% من المتجر ===\n"
        f"- السجلات التجارية / الأرقام الموحدة المكتشفة: {', '.join(cr_numbers) if cr_numbers else 'لم يُرصد رقم سجل'}\n"
        f"- الرقم الضريبي المكتشف: {', '.join(vat_numbers) if vat_numbers else 'لم يُرصد رقم ضريبي'}\n"
        f"- التوثيق في منصة الأعمال (المركز السعودي للأعمال): {'موجود ومُثبت في ذيل الصفحة' if has_saudi_business else 'غير ظاهر نصياً'}\n"
        f"- أرقام الهواتف/الواتساب المكتشفة: {', '.join(phones) if phones else 'لم يُرصد رقم'}\n"
        f"- البريد الإلكتروني المكتشف: {', '.join(emails) if emails else 'لم يُرصد بريد إلكتروني'}\n"
    )
    
    return f"=== الصفحة الرئيسية وذيل الصفحة ===\n{header_and_footer}\n{subpages_content}{auto_extracted}"

def get_available_models(client):
    available = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" in name and not any(x in name for x in ["image", "vision", "embedding", "aqa", "tts", "audio", "robotics"]):
                available.append(name)
    except Exception:
        pass
    available.sort(key=lambda x: 1 if "lite" in x else (2 if "flash" in x else 3))
    return available if available else ["gemini-3.8-flash"]

def analyze_smart(store_data, api_key, status_box):
    client = genai.Client(api_key=api_key.strip())
    
    system_instruction = """
    أنت مستشار قانوني خبير في نظام التجارة الإلكترونية السعودي ولائحته التنفيذية الصادرة عن وزارة التجارة والمركز السعودي للأعمال.
    مهمتك فحص البيانات المُستخرجة بدقة متناهية. اعتمد أولاً على قسم (بيانات قانونية وتواصل تم رصدها آلياً بدقة 100%) وعلى محتوى الصفحات المرفقة.
    
    قائمة الفحص الإلزامية:
    1. الإفصاح عن الهوية (السجل التجاري أو الرقم الموحد 700، والتوثيق في منصة الأعمال).
    2. الرقم الضريبي (15 رقماً).
    3. سياسة الاستبدال والاسترجاع (الالتزام بحق الفسخ خلال 7 أيام وعدم وجود شروط مخالفة).
    4. سياسة الشحن والتوصيل (توضيح مدة التوصيل وحق الإلغاء عند التأخير لأكثر من 15 يوماً).
    5. سياسة الخصوصية وحماية البيانات الشخصية.
    6. بيانات التواصل وآلية الشكاوى (اذكر الأرقام والإيميلات التي تم العثور عليها بالتحديد).
    
    نظم التقرير باللغة العربية في الأقسام التالية:
    - **نسبة الامتثال التقديرية ومستوى الخطورة**
    - **جدول الفحص السريع:** (البند | الحالة: ممتثل ✅ أو مخالفة ⚠️ أو مفقود ❌ | الملاحظة الدقيقة مع ذكر كافة الأرقام والإيميلات المكتشفة)
    - **الملاحظات والثغرات القانونية المكتشفة (إن وجدت)**
    - **النصوص القانونية الجاهزة (انسخ والصق لتصحيح أو استكمال أي نقص)**
    """
    
    prompt = f"افحص بيانات المتجر التالي بدقة وأصدر التقرير القانوني:\n\n{store_data}"
    models_list = get_available_models(client)
    last_error = ""
    
    for model_name in models_list:
        try:
            status_box.info(f"⏳ جاري التحليل القانوني الدقيق باستخدام المحرك: `{model_name}`...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                )
            )
            if response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"API_ERROR: جميع المحركات مزدحمة حالياً. آخر خطأ: {last_error}"

st.title("🛡️ منصة ثقة AI - فاحص امتثال المتاجر الإلكترونية")
st.markdown("##### افحص متجرك الإلكتروني وتأكد من مطابقته لاشتراطات وزارة التجارة السعودية والمركز السعودي للأعمال في ثوانٍ.")

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("أدخل مفتاح Gemini API:", type="password")
    st.info("💡 في النسخة التجارية سنخفي هذا الحقل ونحفظ المفتاح سرياً في السيرفر.")

store_url = st.text_input("أدخل رابط المتجر الإلكتروني (مثال: https://alhulafa.com):", placeholder="https://...")

if st.button("🔍 ابدأ الفحص القانوني الشامل", type="primary"):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح Gemini API في القائمة الجانبية أولاً.")
    elif not store_url or not store_url.startswith("http"):
        st.error("⚠️ يرجى إدخال رابط متجر صحيح يبدأ بـ http:// أو https://")
    else:
        status_placeholder = st.empty()
        status_placeholder.info("🌐 جاري تشغيل المتصفح السحابي لفحص المتجر وذيل الصفحة والسياسات...")
        scraped_data = extract_contact_and_policies(store_url.strip())
            
        if scraped_data.startswith("ERROR:"):
            status_placeholder.error(f"تعذر الوصول إلى المتجر. التفاصيل: {scraped_data}")
        else:
            report = analyze_smart(scraped_data, api_key, status_placeholder)
            
            if report.startswith("API_ERROR:"):
                status_placeholder.error(f"⚠️ {report}")
            else:
                status_placeholder.success("✅ اكتمل الفحص القانوني بنجاح!")
                st.markdown("---")
                st.markdown(report)
                
                st.download_button(
                    label="📥 تحميل التقرير والسياسات الجاهزة (ملف نصي)",
                    data=report,
                    file_name="تقرير_امتثال_المتجر.md",
                    mime="text/markdown"
                )
