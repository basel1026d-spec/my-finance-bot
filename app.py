import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from textblob import TextBlob
from newsapi import NewsApiClient
from sklearn.linear_model import LinearRegression
from datetime import timedelta

# إعدادات الصفحة
st.set_page_config(page_title="محلل الأسواق الذكي", layout="wide")

class FinanceBot:
    def __init__(self):
        try:
            self.news_api_key = st.secrets["NEWS_API_KEY"]
            self.newsapi = NewsApiClient(api_key=self.news_api_key)
        except:
            st.error("خطأ: لم يتم العثور على NEWS_API_KEY")

    def get_live_data(self, ticker):
        try:
            # نسحب بيانات 6 شهور للتدريب
            data = yf.download(ticker, period="6mo", interval="1d")
            return data
        except Exception as e:
            return None

    def predict_next_price(self, data):
        """تنبؤ رياضي بسيط باستخدام الانحدار الخطي"""
        try:
            df = data[['Close']].reset_index()
            df['Day_Num'] = np.arange(len(df))
            
            X = df[['Day_Num']].values
            y = df['Close'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # التنبؤ باليوم القادم
            next_day = np.array([[len(df)]])
            prediction = model.predict(next_day)
            return prediction[0]
        except:
            return None

    def analyze_sentiment(self, query):
        try:
            articles = self.newsapi.get_everything(q=query, language='en', sort_by='relevancy')
            if articles['status'] == 'ok' and articles['totalResults'] > 0:
                sentiments = [TextBlob(art['title']).sentiment.polarity for art in articles['articles'][:5]]
                return np.mean(sentiments)
            return 0
        except:
            return 0

# الواجهة
st.title("📈 مساعد الاستثمار الذكي والتنبؤ")
bot = FinanceBot()

ticker = st.text_input("رمز العملة (مثلاً USDILS=X):", "USDILS=X")
search_query = st.text_input("كلمة البحث للأخبار:", "Israel Economy")

if st.button("بدء التحليل والتنبؤ"):
    with st.spinner('جاري معالجة البيانات والرياضيات...'):
        data = bot.get_live_data(ticker)
        
        if data is not None and not data.empty:
            st.subheader(f"السعر الحالي لـ {ticker}: {data['Close'][-1]:.4f}")
            st.line_chart(data['Close'])
            
            # التنبؤ الرياضي
            predicted_price = bot.predict_next_price(data)
            sentiment_score = bot.analyze_sentiment(search_query)
            
            # عرض النتائج
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("السعر المتوقع (حسابياً)", f"{predicted_price:.4f}")
                st.info("هذا التنبؤ يعتمد على الاتجاه الخطي للأسعار السابقة.")

            with col2:
                status = "إيجابي" if sentiment_score > 0.05 else "سلبي" if sentiment_score < -0.05 else "محايد"
                st.metric("نبض الأخبار (Sentiment)", status)
            
            # الخلاصة الهندسية
            st.subheader("🤖 التوصية التقنية")
            current_price = data['Close'][-1]
            if predicted_price > current_price and sentiment_score > 0:
                st.success("إشارة شراء قوية: التحليل الرياضي والأخبار يتفقان على الصعود.")
            elif predicted_price < current_price and sentiment_score < 0:
                st.error("إشارة حذر: التحليل الرياضي والأخبار يتفقان على الهبوط.")
            else:
                st.warning("إشارة مختلطة: يفضل الانتظار أو مراقبة السوق المحلي.")
        else:
            st.error("تعذر جلب البيانات. تأكد من الرمز.")
