import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google import genai
from google.genai import types

st.set_page_config(page_title="ثقة AI | فاحص امتثال المتاجر السعودية", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    body, .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stTextInput > div > div > input {
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
        
        main_text = soup.get_text(separator=' ', strip=True)[:6000]
        
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
                        sub_res = requests.get(full_url, headers=headers, timeout=10)
                        sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
                        sub_text = sub_soup.get_text(separator=' ', strip=True)[:3500]
                        policy_texts += f"\n--- محتوى صفحة ({link_text}) ---\n{sub_text}\n"
                    except:
                        continue
                    if len(visited_urls) >= 4:
                        break
                        
        return f"بيانات الصفحة الرئيسية والذيل (Footer):\n{main_text}\n\n{policy_texts}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def analyze_compliance(store_data, api_key):
    clean_key = api_key.strip()
    client = genai.Client(api_key=clean_key)
    
    system_instruction = """
    أنت مستشار قانوني خبير في نظام التجارة الإلكترونية السعودي ولائحته التنفيذية الصادرة عن وزارة التجارة والمركز السعودي للأعمال.
    مهمتك فحص النصوص المستخرجة من متجر إلكتروني سعودي وتقييم مدى امتثاله للاشتراطات النظامية.
    
    قائمة الفحص الإلزامية:
    1. الإفصاح عن الهوية (السجل التجاري أو وثيقة العمل الحر، ورقم التوثيق في منصة الأعمال).
    2. الرقم الضريبي (إن وجد أو الإشارة إليه).
    3. سياسة الاستبدال والاسترجاع (هل تلتزم بحق المستهلك في الفسخ خلال 7 أيام؟ وهل تحتوي على عبارات مخالفة مثل "لا يوجد استرجاع" على منتجات غير مستثناة؟).
    4. سياسة الشحن والتوصيل (هل توضح مدة التوصيل وحق الإلغاء عند التأخير لأكثر من 15 يوماً؟).
    5. سياسة الخصوصية وحماية البيانات الشخصية.
    6. آلية استقبال الشكاوى وبيانات التواصل (هاتف، بريد إلكتروني، مدة معالجة الشكوى).
    
    يجب أن يكون مخرجك منظماً باللغة العربية الاحترافية ويحتوي على الأقسام التالية:
    - **نسبة الامتثال التقديرية:** (مثلاً: 60%) مع تقييم مستوى الخطورة (منخفض / متوسط / مرتفع).
    - **جدول الفحص التفصيلي:** يوضح كل بند وحالته (ممتثل ✅ / مخالفة ⚠️ / مفقود ❌) مع السبب.
    - **المخالفات الحرجة التي قد تعرض المتجر للغرامة:** شرح مبسط لكل ثغرة.
    - **الحلول الجاهزة (انسخ والصق):** اكتب للتاجر صياغة قانونية احترافية ومطابقة لنظام وزارة التجارة السعودي لكل سياسة ناقصة أو مخالفة ليقوم بوضعها في متجره فوراً.
    """
    
    prompt = f"قم بفحص بيانات المتجر الإلكتروني التالي وأصدر التقرير القانوني الكامل:\n\n{store_data}"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        return f"API_ERROR: {str(e)}"

st.title("🛡️ منصة ثقة AI - فاحص امتثال المتاجر الإلكترونية")
st.subheader("افحص متجرك الإلكتروني وتأكد من مطابقته لاشتراطات وزارة التجارة السعودية والمركز السعودي للأعمال في ثوانٍ.")

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("أدخل مفتاح Gemini API:", type="password", help="يمكنك الحصول عليه مجاناً من Google AI Studio")
    st.info("💡 **نصيحة للمشرف:** في النسخة التجارية للعملاء، سنقوم بوضع مفتاحك في متغيرات البيئة ولن يظهر هذا الحقل للعميل.")

store_url = st.text_input("أدخل رابط المتجر الإلكتروني (مثال: https://example.salla.sa):", placeholder="https://...")

if st.button("🔍 ابدأ الفحص القانوني الشامل", type="primary"):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح Gemini API في القائمة الجانبية أولاً.")
    elif not store_url or not store_url.startswith("http"):
        st.error("⚠️ يرجى إدخال رابط متجر صحيح يبدأ بـ http:// أو https://")
    else:
        with st.spinner("جاري قراءة صفحات المتجر، فحص التذييل (Footer)، وتحليل السياسات القانونية..."):
            scraped_data = scrape_store_content(store_url.strip())
            
            if scraped_data.startswith("ERROR:"):
                st.error(f"تعذر الوصول إلى المتجر. التفاصيل: {scraped_data}")
            else:
                st.success("✅ تم سحب بيانات المتجر بنجاح! جاري التحليل القانوني...")
                report = analyze_compliance(scraped_data, api_key)
                
                if report.startswith("API_ERROR:"):
                    st.error(f"⚠️ حدث خطأ من مفتاح الذكاء الاصطناعي: {report}")
                    st.warning("تأكد من نسخ المفتاح بالكامل من Google AI Studio بدون نقص، أو أنشئ مفتاحاً جديداً.")
                else:
                    st.markdown("---")
                    st.markdown(report)
                    
                    st.download_button(
                        label="📥 تحميل التقرير والسياسات الجاهزة (ملف نصي)",
                        data=report,
                        file_name="تقرير_امتثال_المتجر.md",
                        mime="text/markdown"
                    )
