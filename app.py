import time
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from google import genai
from google.genai import types

st.set_page_config(page_title="ثقة AI | فاحص امتثال المتاجر السعودية", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
    body, .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stTextInput > div > div > input {
        text-align: right;
    }
    h1, h2, h3, p, div {
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

def scrape_store_content(base_url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        full_text = soup.get_text(separator=' ', strip=True)
        # أخذ بداية الصفحة + نهاية الصفحة (لضمان التقاط ذيل الصفحة Footer بالكامل)
        if len(full_text) > 7000:
            main_text = full_text[:2500] + "\n\n... [ذيل الصفحة والمعلومات القانونية] ...\n\n" + full_text[-4500:]
        else:
            main_text = full_text

        # استخراج الروابط المهمة في ذيل الصفحة (مثل رابط المركز السعودي للأعمال، واتساب، إيميل، صفحات السياسات)
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc.replace("www.", "")
        
        policy_keywords = [
            'استرجاع', 'استبدال', 'خصوصية', 'شروط', 'سياسة', 'شكاوى', 'تواصل', 'من نحن', 'شحن', 'توصيل',
            'return', 'refund', 'privacy', 'terms', 'policy', 'shipping', 'contact', 'about'
        ]
        
        important_links = []
        policy_texts = ""
        visited_urls = set([base_url, base_url.rstrip('/')])
        
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            link_text = link.get_text(strip=True)
            full_url = urljoin(base_url, href)
            
            # التقاط روابط التوثيق الخارجية (المركز السعودي للأعمال / معروف) وروابط التواصل
            if any(ext in href.lower() for ext in ['eauthenticate', 'saudibusiness', 'maroof', 'mailto:', 'tel:', 'wa.me', 'whatsapp']):
                important_links.append(f"رابط توثيق/تواصل ({link_text}): {href}")
                
            # التقاط صفحات السياسات الداخلية
            if any(kw in link_text.lower() or kw in href.lower() for kw in policy_keywords) and full_url not in visited_urls:
                if base_domain in urlparse(full_url).netloc and full_url.startswith("http"):
                    visited_urls.add(full_url)
                    try:
                        sub_res = requests.get(full_url, headers=headers, timeout=10)
                        sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
                        sub_text = sub_soup.get_text(separator=' ', strip=True)[:3500]
                        policy_texts += f"\n--- محتوى صفحة ({link_text or full_url}) ---\n{sub_text}\n"
                    except:
                        continue
                    if len(visited_urls) >= 6:
                        break
                        
        links_summary = "\n".join(set(important_links))
        return f"بيانات الصفحة الرئيسية وذيل الصفحة (Footer):\n{main_text}\n\nالروابط الخارجية والتواصل المستخرجة:\n{links_summary}\n\n{policy_texts}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_available_models(client):
    available = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" in name and not any(x in name for x in ["image", "vision", "embedding", "aqa", "tts", "audio", "robotics"]):
                available.append(name)
    except Exception:
        pass
    
    def priority(model_name):
        if "lite" in model_name:
            return 1
        if "flash" in model_name:
            return 2
        return 3
        
    available.sort(key=priority)
    return available if available else ["gemini-3.8-flash"]

def analyze_smart(store_data, api_key, status_box):
    clean_key = api_key.strip()
    client = genai.Client(api_key=clean_key)
    
    system_instruction = """
    أنت مستشار قانوني خبير في نظام التجارة الإلكترونية السعودي ولائحته التنفيذية الصادرة عن وزارة التجارة والمركز السعودي للأعمال.
    مهمتك فحص النصوص والروابط المستخرجة بدقة متناهية وتقييم مدى امتثال المتجر للاشتراطات النظامية.
    تحقق بعناية من ذيل الصفحة والروابط المستخرجة والصفحات الفرعية قبل الحكم بأن أي بند مفقود.
    
    قائمة الفحص الإلزامية:
    1. الإفصاح عن الهوية (السجل التجاري أو وثيقة العمل الحر، أو رابط/رقم التوثيق في المركز السعودي للأعمال eauthenticate).
    2. الرقم الضريبي (15 رقماً).
    3. سياسة الاستبدال والاسترجاع (هل توجد سياسة؟ وهل تلتزم بحق المستهلك في الفسخ خلال 7 أيام؟).
    4. سياسة الشحن والتوصيل (هل توضح مدة التوصيل وحق الإلغاء عند التأخير لأكثر من 15 يوماً؟).
    5. سياسة الخصوصية وحماية البيانات الشخصية.
    6. آلية استقبال الشكاوى وبيانات التواصل (هاتف، واتساب، بريد إلكتروني، مدة معالجة الشكوى).
    
    نظم التقرير باللغة العربية في الأقسام التالية:
    - **نسبة الامتثال التقديرية ومستوى الخطورة**
    - **جدول الفحص السريع:** (البند | الحالة: ممتثل ✅ أو مخالفة ⚠️ أو مفقود ❌ | الملاحظة الدقيقة مع ذكر الأرقام أو الروابط المكتشفة)
    - **الملاحظات والثغرات القانونية المكتشفة (إن وجدت)**
    - **النصوص القانونية الجاهزة (انسخ والصق لتصحيح أو استكمال أي نقص)**
    """
    
    prompt = f"افحص بيانات المتجر التالي بدقة وأصدر التقرير القانوني:\n\n{store_data}"
    
    models_list = get_available_models(client)
    last_error = ""
    
    for model_name in models_list:
        try:
            status_box.info(f"⏳ جاري الفحص القانوني الدقيق باستخدام المحرك: `{model_name}`...")
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
            
    return f"API_ERROR: جميع المحركات المتاحة مزدحمة حالياً. آخر خطأ: {last_error}"

st.title("🛡️ منصة ثقة AI - فاحص امتثال المتاجر الإلكترونية")
st.markdown("##### افحص متجرك الإلكتروني وتأكد من مطابقته لاشتراطات وزارة التجارة السعودية والمركز السعودي للأعمال في ثوانٍ.")

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("أدخل مفتاح Gemini API:", type="password")
    st.info("💡 في النسخة التجارية سنخفي هذا الحقل ونحفظ المفتاح سرياً في السيرفر.")

store_url = st.text_input("أدخل رابط المتجر الإلكتروني (مثال: https://deemahstore.sa/ar):", placeholder="https://...")

if st.button("🔍 ابدأ الفحص القانوني الشامل", type="primary"):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح Gemini API في القائمة الجانبية أولاً.")
    elif not store_url or not store_url.startswith("http"):
        st.error("⚠️ يرجى إدخال رابط متجر صحيح يبدأ بـ http:// أو https://")
    else:
        status_placeholder = st.empty()
        status_placeholder.info("🌐 جاري سحب ذيل الصفحة (Footer) وجميع صفحات السياسات القانونية...")
        scraped_data = scrape_store_content(store_url.strip())
            
        if scraped_data.startswith("ERROR:"):
            status_placeholder.error(f"تعذر الوصول إلى المتجر. التفاصيل: {scraped_data}")
        else:
            report = analyze_smart(scraped_data, api_key, status_placeholder)
            
            if report.startswith("API_ERROR:"):
                status_placeholder.error(f"⚠️ {report}")
            else:
                status_placeholder.success("✅ اكتمل الفحص القانوني الدقيق بنجاح!")
                st.markdown("---")
                st.markdown(report)
                
                st.download_button(
                    label="📥 تحميل التقرير والسياسات الجاهزة (ملف نصي)",
                    data=report,
                    file_name="تقرير_امتثال_المتجر.md",
                    mime="text/markdown"
                )
