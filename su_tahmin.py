# Dosya Adı: su_tahmin.py (REST API V2 - BASİTLEŞTİRİLMİŞ SORGULAMA)
import streamlit as st
import pandas as pd
from datetime import datetime
import requests # REST API için yeni kütüphane
import json 
from io import StringIO 
# Eski Firebase kütüphaneleri (firebase_admin, credentials, firestore) KALDIRILDI

# Firestore REST API için gerekli ayarlar
PROJECT_ID = "akillisutakip" # Firebase Proje ID'niz
KOLEKSIYON_ADI = 'su_okumalar' 
ROLLING_WINDOW = 7 
ABONE_ID = "ABONE_0001" # Şimdilik sabit abone

from tahmin_kodu import tahmin_yap 

st.set_page_config(layout="wide")
st.title("💧 Akıllı Su Tüketimi İzleme ve Tahmin (REST API)")

# --- REST API İLE VERİ ÇEKME FONKSİYONU ---
@st.cache_data(ttl=600) # Veriyi 10 dakika önbelleğe al
def fetch_data_from_firestore_rest(abone_id):
    # DİKKAT: Artık sadece koleksiyonun tümünü okuyoruz. Filtreleme Python'da yapılacak.
    # Bu yöntem, 400 Bad Request hatasını çözmek için en garantili yoldur.
    URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{KOLEKSIYON_ADI}"
    
    try:
        # GET isteği ile tüm koleksiyonu çekiyoruz
        response = requests.get(URL)
        response.raise_for_status() # HTTP hatalarını yakalar

        results = response.json()
        
        veri_listesi = []
        # 'documents' anahtarının varlığını kontrol et
        if 'documents' in results:
            for item in results['documents']:
                fields = item.get('fields', {})
                
                # Firestore'dan gelen veriyi doğru formatta alıyoruz
                tuketim_value = fields.get('tuketim', {}).get('doubleValue')
                if tuketim_value is None:
                    tuketim_value = fields.get('tuketim', {}).get('integerValue')
                
                abone_id_val = fields.get('abone_id', {}).get('stringValue')
                timestamp_val = fields.get('timestamp', {}).get('stringValue')
                
                # Veriyi alırken ABONE_ID filtrelemesini yapıyoruz
                if tuketim_value is not None and timestamp_val and abone_id_val == abone_id:
                    veri_listesi.append({
                        "tarih": datetime.strptime(timestamp_val, '%Y-%m-%d %H:%M:%S'),
                        "tuketim": float(tuketim_value)
                    })
        
        return pd.DataFrame(veri_listesi)

    except requests.exceptions.RequestException as err:
        st.error(f"🔴 KRİTİK HATA: Firestore REST API hatası. Lütfen Firebase Kurallarınızı ve Ağ Bağlantısını kontrol edin. Hata: {err}")
        return None
    except Exception as e:
        st.error(f"🔴 KRİTİK HATA: Veri işleme hatası. Hata: {e}")
        return None


# --- ANA UYGULAMA AKIŞI ---
veri_var_mi = False
df = fetch_data_from_firestore_rest(ABONE_ID)

if df is not None and not df.empty:
    veri_var_mi = True
    df = df.sort_values("tarih")
    
    # Günlük Tüketimi Hesapla
    df["gun"] = df["tarih"].dt.date
    gunluk = df.groupby("gun")["tuketim"].sum().reset_index()
    son_tarih = df["tarih"].iloc[-1]
    
    st.subheader(f"Günlük Su Tüketimi Grafiği ({ABONE_ID})")
    st.line_chart(gunluk.set_index("gun")["tuketim"], use_container_width=True)
    st.markdown(f"**Son Veri Zamanı:** {son_tarih.strftime('%d-%m-%Y %H:%M')}")
    
    # TAHMİN BÖLÜMÜ
    try:
        # tahmin_kodu.py'deki fonksiyonu çağırıyoruz
        gunluk_tahmin, haftalik_tahmin, aylik_tahmin = tahmin_yap(df.copy()) # Kopyayı gönderiyoruz

        st.subheader("💧 Tahmini Su Tüketimi")
        col1, col2, col3 = st.columns(3)

        if gunluk_tahmin > 0:
            col1.metric("Yarın Tahmini Tüketim", f"{gunluk_tahmin:.2f} Lt")
        else:
            col1.info("Yeterli veri yok (en az 7 gün).")
            
        col2.metric("Haftalık Tahmini Tüketim", f"{haftalik_tahmin:.2f} Lt")
        col3.metric("Aylık Tahmini Tüketim", f"{aylik_tahmin:.2f} Lt")
    
    except Exception as e:
        st.error(f"Tahmin hesaplanırken bir hata oluştu: {e}")

else:
    # Bu hata, hem veri yoksa hem de 404/403 (kurallar) hatası alınırsa gösterilir.
    st.warning("Veritabanında bu aboneye ait veri bulunamadı veya bağlantı kurulamadı. Lütfen Firebase Kurallarını kontrol edin.")
