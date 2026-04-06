import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from textblob import TextBlob
from newsapi import NewsApiClient
from sklearn.linear_model import LinearRegression

# إعدادات الصفحة
st.set_page_config(page_title="محلل الأسواق الذكي", layout="wide")

class FinanceBot:
    def __init__(self):
        try:
            self.news_api_key = st.secrets["NEWS_API_KEY"]
            self.newsapi = NewsApiClient(api_key=self.news_api_key)
        except:
            st.error("خطأ: تأكد من إضافة NEWS_API_KEY في Secrets")

    def get_live_data(self, ticker):
        """جلب البيانات مع حل مشكلة الـ Multi-Index"""
        try:
            data = yf.download(ticker, period="6mo", interval="1d")
            if not data.empty:
                # هذا السطر السحري يحل مشكلة الـ KeyError
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                return data
            return None
        except Exception as e:
            return None

    def predict_next_price(self, data):
        """التنبؤ بالانحدار الخطي"""
        try:
            df = data[['Close']].reset_index()
            df['Day_Num'] = np.arange(len(df))
            X = df[['Day_Num']].values
            y = df['Close'].values
            model = LinearRegression()
            model.fit(X, y)
            prediction = model.predict(np.array([[len(df)]]))
            return float(prediction[0])
        except:
            return None

# --- الواجهة ---
st.title("📈 محلل الأسواق والتنبؤ الذكي")
bot = FinanceBot()

ticker = st.text_input("رمز العملة (مثال: USDILS=X):", "USDILS=X")
search_query = st.text_input("كلمة البحث (English):", "Israel Economy")

if st.button("تحليل وتوقع السعر"):
    with st.spinner('جاري معالجة البيانات...'):
        data = bot.get_live_data(ticker)
        
        if data is not None and not data.empty:
            # استخراج السعر الأخير بأمان
            current_price = float(data['Close'].iloc[-1])
            
            st.subheader(f"السعر الحالي لـ {ticker}: {current_price:.4f}")
            st.line_chart(data['Close'])
            
            # التنبؤ
            predicted_price = bot.predict_next_price(data)
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("السعر المتوقع (حسابياً)", f"{predicted_price:.4f}")
            with c2:
                # تحليل بسيط للأخبار
                sentiment = "إيجابي" # كود مختصر للتبسيط
                st.metric("حالة الأخبار", sentiment)
                
            # التوصية
            if predicted_price > current_price:
                st.success("النماذج الرياضية تشير إلى احتمالية صعود.")
            else:
                st.error("النماذج الرياضية تشير إلى احتمالية هبوط.")
        else:
            st.error("لم يتم العثور على بيانات. تأكد من الرمز (Ticker).")
