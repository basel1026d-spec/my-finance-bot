import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from textblob import TextBlob
from newsapi import NewsApiClient

# إعدادات الصفحة
st.set_page_config(page_title="محلل الأسواق الذكي", layout="wide")

class FinanceBot:
    def __init__(self):
        # جلب المفتاح السري من إعدادات Streamlit Cloud
        try:
            self.news_api_key = st.secrets["NEWS_API_KEY"]
            self.newsapi = NewsApiClient(api_key=self.news_api_key)
        except:
            st.error("خطأ: لم يتم العثور على NEWS_API_KEY في Secrets")

    def get_live_data(self, ticker):
        """جلب البيانات من ياهو فاينانس مع معالجة الأخطاء"""
        try:
            # استخدمنا 1d (يوم واحد) لتجنب حظر ياهو المتكرر في السيرفرات
            data = yf.download(ticker, period="6mo", interval="1d")
            return data
        except Exception as e:
            st.error(f"فشل في جلب البيانات من Yahoo Finance: {e}")
            return None

    def analyze_sentiment(self, query):
        """تحليل معنويات الأخبار"""
        try:
            articles = self.newsapi.get_everything(q=query, language='en', sort_by='relevancy')
            if articles['status'] == 'ok' and articles['totalResults'] > 0:
                sentiments = []
                for art in articles['articles'][:5]:
                    analysis = TextBlob(art['title'])
                    sentiments.append(analysis.sentiment.polarity)
                return np.mean(sentiments)
            return 0
        except:
            return 0

# تشغيل الواجهة
st.title("📈 مساعد الاستثمار الذكي")
st.markdown("---")

bot = FinanceBot()

# مدخلات المستخدم
col1, col2 = st.columns(2)
with col1:
    ticker = st.text_input("أدخل رمز العملة أو السهم (مثلاً: GC=F للذهب، BTC-USD للبتكوين):", "GC=F")
with col2:
    search_query = st.text_input("كلمة البحث للأخبار (بالإنجليزي):", "Gold market")

if st.button("تحليل الآن"):
    with st.spinner('جاري تحليل البيانات...'):
        # 1. جلب البيانات المالية
        data = bot.get_live_data(ticker)
        
        if data is not None and not data.empty:
            # عرض الرسم البياني
            st.subheader(f"حركة السعر لـ {ticker}")
            st.line_chart(data['Close'])
            
            # 2. تحليل الأخبار
            sentiment_score = bot.analyze_sentiment(search_query)
            
            #
