import time
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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
        response = requests.get(base_url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        main_text = soup.get_text(separator=' ', strip=True)[:4500]
        
        policy_keywords = ['استرجاع', 'استبدال', 'خصوصية', 'شروط', 'سياسة', 'شكاوى', 'return', 'refund', 'privacy', 'terms']
        policy_texts = ""
        visited_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            full_url = urljoin(base_url, href)
            
            if any(kw in link_text or kw in href.lower() for kw in policy_keywords) and full_url not in visited_urls:
                if base_url in full_url:
                    visited_urls.add(full_url)
                    try:
                        sub_res = requests.get(full_url, headers=headers, timeout=8)
                        sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
                        sub_text = sub_soup.get_text(separator=' ', strip=True)[:2500]
                        policy_texts += f"\n--- محتوى صفحة ({link_text}) ---\n{sub_text}\n"
                    except:
                        continue
                    if len(visited_urls) >= 3:
                        break
                        
        return f"بيانات الصفحة الرئيسية والذيل (Footer):\n{main_text}\n\n{policy_texts}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def analyze_with_retry(store_data, api_key, status_box):
    clean_key = api_key.strip()
    client = genai.Client(api_key=clean_key)
    
    system_instruction = """
    أنت مستشار قانوني خبير في نظام التجارة الإلكترونية السعودي ولائحته التنفيذية الصادرة عن وزارة التجارة والمركز السعودي للأعمال.
    مهمتك فحص النصوص المستخرجة من متجر إلكتروني سعودي وتقييم مدى امتثاله للاشتراطات النظامية باختصار ووضوح واحترافية.
    
    قائمة الفحص الإلزامية:
    1. الإفصاح عن الهوية (السجل التجاري أو وثيقة العمل الحر، ورقم التوثيق في منصة الأعمال).
    2. الرقم الضريبي (إن وجد).
    3. سياسة الاستبدال والاسترجاع (حق الفسخ خلال 7 أيام وعدم وجود عبارات مخالفة).
    4. سياسة الشحن والتوصيل (مدة التوصيل وحق الإلغاء عند التأخير لأكثر من 15 يوماً).
    5. سياسة الخصوصية وحماية البيانات.
    6. آلية استقبال الشكاوى وبيانات التواصل.
    
    نظم التقرير باللغة العربية في الأقسام التالية:
    - **نسبة الامتثال التقديرية ومستوى الخطورة**
    - **جدول الفحص السريع:** (البند | الحالة: ممتثل ✅ أو مخالفة ⚠️ أو مفقود ❌ | الملاحظة)
    - **أهم المخالفات التي تعرض المتجر للغرامة**
    - **النصوص القانونية الجاهزة (انسخ والصق لتصحيح المتجر فوراً)**
    """
    
    prompt = f"افحص بيانات المتجر التالي وأصدر التقرير القانوني:\n\n{store_data}"
    
    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
            status_box.info(f"⏳ جاري التحليل القانوني عبر الذكاء الاصطناعي (المحاولة {attempt} من {max_retries})...")
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
            )
            return response.text
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg:
                if attempt < max_retries:
                    status_box.warning(f"السيرفر مزدحم حالياً، جاري إعادة المحاولة تلقائياً خلال 4 ثوانٍ... ({attempt}/{max_retries})")
                    time.sleep(4)
                    continue
            return f"API_ERROR: {err_msg}"
            
    return "API_ERROR: السيرفر مزدحم حالياً بعد عدة محاولات، يرجى المحاولة بعد دقيقة."

st.title("🛡️ منصة ثقة AI - فاحص امتثال المتاجر الإلكترونية")
st.markdown("##### افحص متجرك الإلكتروني وتأكد من مطابقته لاشتراطات وزارة التجارة السعودية والمركز السعودي للأعمال في ثوانٍ.")

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("أدخل مفتاح Gemini API:", type="password")
    st.info("💡 في النسخة التجارية سنخفي هذا الحقل ونحفظ المفتاح سرياً في السيرفر.")

store_url = st.text_input("أدخل رابط المتجر الإلكتروني (مثال: https://blacksipcoffee.com):", placeholder="https://...")

if st.button("🔍 ابدأ الفحص القانوني الشامل", type="primary"):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح Gemini API في القائمة الجانبية أولاً.")
    elif not store_url or not store_url.startswith("http"):
        st.error("⚠️ يرجى إدخال رابط متجر صحيح يبدأ بـ http:// أو https://")
    else:
        status_placeholder = st.empty()
        status_placeholder.info("🌐 جاري قراءة صفحات المتجر وفحص التذييل (Footer)...")
        scraped_data = scrape_store_content(store_url.strip())
            
        if scraped_data.startswith("ERROR:"):
            status_placeholder.error(f"تعذر الوصول إلى المتجر. التفاصيل: {scraped_data}")
        else:
            report = analyze_with_retry(scraped_data, api_key, status_placeholder)
            
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
