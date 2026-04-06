import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from textblob import TextBlob
from newsapi import NewsApiClient
from datetime import datetime
from sklearn.linear_model import LinearRegression

# --- إعدادات البرنامج ---
# استبدل 'YOUR_API_KEY' بمفتاحك الخاص من NewsAPI
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
SYMBOL = "USDILS=X"

st.set_page_config(page_title="محلل الدولار/شيكل المهندس", layout="wide")

class FinanceBot:
    def __init__(self):
        try:
            self.newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        except:
            self.newsapi = None

    def get_live_data(self):
        # جلب البيانات لآخر 7 أيام (ساعة بساعة)
data = yf.download(ticker, period="6mo", interval="1d")     
# تنظيف الأعمدة لتجنب مشاكل الإصدارات الجديدة
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data

    def analyze_technical(self, data):
        # حساب المتوسط المتحرك لـ 20 ساعة
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        
        # استخراج القيم والتأكد أنها أرقام نقيّة (float)
        current_price = float(data['Close'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2])
        sma_20_val = float(data['SMA_20'].iloc[-1])
        
        trend = "صاعد" if current_price > sma_20_val else "هابط"
        change = ((current_price - prev_price) / prev_price) * 100
        
        return current_price, trend, change

    def predict_future(self, data):
        """ ميزة التوقع الرياضي باستخدام الانحدار الخطي """
        y = data['Close'].values.reshape(-1, 1)
        x = np.arange(len(y)).reshape(-1, 1)
        
        model = LinearRegression()
        model.fit(x, y)
        
        # توقع السعر لـ 5 خطوات زمنية قادمة (5 ساعات)
        future_step = np.array([[len(y) + 5]])
        prediction = model.predict(future_step)
        return float(prediction[0][0])

    def get_geopolitical_news(self):
        try:
            news = self.newsapi.get_everything(q='Israel OR Shekel OR Fed Rate',
                                              language='en',
                                              sort_by='publishedAt')
            articles = news['articles'][:5]
            sentiment_score = 0
            titles = []
            for art in articles:
                analysis = TextBlob(art['title'])
                sentiment_score += analysis.sentiment.polarity
                titles.append(art['title'])
            
            avg_sentiment = sentiment_score / len(articles) if articles else 0
            return avg_sentiment, titles
        except:
            return 0, ["لا توجد أخبار حية حالياً (تحقق من المفتاح)"]

    def final_decision(self, tech_trend, sentiment, prediction, current_price):
        # دمج التحليل الفني، المشاعر، والتوقع الرياضي
        if tech_trend == "صاعد" and sentiment > 0.05 and prediction > current_price:
            return "شراء (Buy) 🟢", "جميع المؤشرات (الفنية، الأخبار، والتوقع الرياضي) تدعم الارتفاع."
        elif tech_trend == "هابط" and sentiment < -0.05 and prediction < current_price:
            return "بيع (Sell) 🔴", "المسار الهابط مدعوم بالأخبار السلبية وتوقعات النموذج الرياضي."
        else:
            return "انتظار (Hold) 🟡", "هناك تضارب في الإشارات؛ يفضل مراقبة السوق حالياً."

# --- واجهة المستخدم (Streamlit UI) ---
bot = FinanceBot()

st.title("🛡️ نظام دعم القرار الهندسي: USD/ILS")
st.write(f"آخر تحديث للبيانات: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

data = bot.get_live_data()

if not data.empty:
    try:
        # 1. التحليل التقني والتوقع
        price, trend, change = bot.analyze_technical(data)
        prediction = bot.predict_future(data)
        
        # 2. عرض المؤشرات الرئيسية
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("السعر الحالي", f"{price:.4f}", f"{change:.2f}%")
        with col2:
            st.metric("التوقع الرياضي (قريباً)", f"{prediction:.4f}")
        with col3:
            st.info(f"**الاتجاه التقني:** {trend}")

        st.divider()

        # 3. الرسم البياني
        st.subheader("📈 مسار السعر لآخر 7 أيام")
        st.line_chart(data['Close'])

        # 4. الأخبار والقرار النهائي
        col_news, col_decision = st.columns([2, 1])
        
        with col_news:
            st.subheader("🌍 نبض الأخبار العالمية")
            sentiment, news_titles = bot.get_geopolitical_news()
            sentiment_label = "إيجابي للدولار" if sentiment > 0.05 else "سلبي للدولار" if sentiment < -0.05 else "محايد"
            st.write(f"**الحالة العامة:** {sentiment_label}")
            for t in news_titles:
                st.write(f"- {t}")

        with col_decision:
            st.subheader("🤖 قرار النظام")
            decision, reason = bot.final_decision(trend, sentiment, prediction, price)
            st.success(f"### {decision}")
            st.write(f"**السبب:** {reason}")
            
    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
else:
    st.error("فشل في جلب البيانات من Yahoo Finance.")
