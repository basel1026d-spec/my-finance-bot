import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

# إعدادات الصفحة
st.set_page_config(page_title="محلل التوقعات الثلاثية", layout="wide")

class FinanceBot:
    def get_live_data(self, ticker):
        try:
            data = yf.download(ticker, period="6mo", interval="1d")
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                return data
            return None
        except:
            return None

    def predict_future(self, data, days_ahead=3):
        """التنبؤ لعدة أيام قادمة"""
        try:
            df = data[['Close']].reset_index()
            df['Day_Num'] = np.arange(len(df))
            
            X = df[['Day_Num']].values
            y = df['Close'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            predictions = []
            last_date = df['Date'].iloc[-1]
            
            for i in range(1, days_ahead + 1):
                next_day_num = len(df) + i - 1
                pred_price = model.predict(np.array([[next_day_num]]))[0]
                next_date = last_date + timedelta(days=i)
                # تخطي أيام العطلة (السبت والأحد) للمصداقية
                if next_date.weekday() >= 5: 
                    next_date += timedelta(days=2)
                predictions.append({"التاريخ": next_date.strftime('%Y-%m-%d'), "السعر المتوقع": round(float(pred_price), 4)})
            
            return predictions
        except:
            return []

# --- الواجهة ---
st.title("📊 نظام التنبؤ الثلاثي للأسعار")
st.write("يتوقع هذا النظام السعر بناءً على تحليل الاتجاه (Trend Analysis) للأيام الـ 3 القادمة.")

bot = FinanceBot()
ticker = st.text_input("أدخل رمز العملة (مثلاً USDILS=X):", "USDILS=X")

if st.button("تحليل وتوقع الـ 3 أيام القادمة"):
    with st.spinner('جاري حساب المسار الرياضي...'):
        data = bot.get_live_data(ticker)
        
        if data is not None and not data.empty:
            current_price = float(data['Close'].iloc[-1])
            st.metric("السعر الحالي الآن", f"{current_price:.4f}")
            
            # حساب التوقعات
            future_preds = bot.predict_future(data)
            
            st.markdown("---")
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("📅 جدول التوقعات")
                df_preds = pd.DataFrame(future_preds)
                st.table(df_preds)
            
            with col2:
                st.subheader("📈 مسار السعر المتوقع")
                # دمج البيانات الحالية مع التوقعات للرسم
                last_prices = data['Close'].tail(15) # عرض آخر 15 يوم فقط للوضوح
                st.line_chart(last_prices)
                
            # نصيحة هندسية
            st.info(f"💡 ملاحظة: التوقع ليوم {future_preds[-1]['التاريخ']} يعتمد على استمرار الزخم الحالي للسوق.")
        else:
            st.error("تعذر جلب البيانات، تأكد من الرمز.")
