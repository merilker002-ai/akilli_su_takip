# Dosya Adı: su_tahmin.py (YENİ REST API SÜRÜMÜ)
import streamlit as st
import pandas as pd
from datetime import datetime
import requests # Yeni kütüphane
import json 
from io import StringIO # JSON'dan gelen veriyi düzenlemek için

# Firestore REST API için gerekli ayarlar
PROJECT_ID = "akillisutakip"
KOLEKSIYON_ADI = 'su_okumalar' 
ROLLING_WINDOW = 7 
ABONE_ID = "ABONE_0001" # Şimdilik sabit abone

# tahmin_kodu modülünü import ediyoruz
from tahmin_kodu import tahmin_yap 

st.set_page_config(layout="wide")
st.title("💧 Akıllı Su Tüketimi İzleme ve Tahmin (REST API)")

# --- REST API İLE VERİ ÇEKME FONKSİYONU ---
@st.cache_data(ttl=600) # Veriyi 10 dakika önbelleğe al
def fetch_data_from_firestore_rest(abone_id):
    # Firestore REST API'si üzerinden sorgu yapmak için temel URL
    # API key kullanmaya gerek yoktur, çünkü kuralları herkese açtık.
    URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{KOLEKSIYON_ADI}:runQuery"
    
    # Firestore'da 'where' (filtreleme) yapmak için yapı
    query_data = {
        "structuredQuery": {
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "abone_id"},
                    "op": "EQUAL",
                    "value": {"stringValue": abone_id}
                }
            },
            "from": [
                {"collectionId": KOLEKSIYON_ADI}
            ],
            "orderBy": [
                {"field": {"fieldPath": "timestamp"}, "direction": "ASCENDING"}
            ]
        }
    }

    try:
        # Sorguyu POST isteğiyle gönderiyoruz
        response = requests.post(URL, json=query_data)
        response.raise_for_status() # HTTP hatalarını yakalar

        results = response.json()
        
        veri_listesi = []
        for item in results:
            if 'document' in item:
                fields = item['document']['fields']
                
                # Firestore'dan gelen veriyi doğru formatta alıyoruz
                # doubleValue veya integerValue olabilir
                tuketim_value = fields.get('tuketim', {}).get('doubleValue')
                if tuketim_value is None:
                    tuketim_value = fields.get('tuketim', {}).get('integerValue')
                
                # Diğer alanlar
                abone_id_val = fields.get('abone_id', {}).get('stringValue')
                timestamp_val = fields.get('timestamp', {}).get('stringValue')
                
                if tuketim_value is not None and timestamp_val:
                    veri_listesi.append({
                        "tarih": datetime.strptime(timestamp_val, '%Y-%m-%d %H:%M:%S'),
                        "tuketim": float(tuketim_value),
                        "abone_id": abone_id_val
                    })

        return pd.DataFrame(veri_listesi)

    except requests.exceptions.RequestException as err:
        st.error(f"🔴 KRİTİK HATA: Firestore REST API hatası. Lütfen Firebase Kurallarınızı ve Ağ Bağlantısını kontrol edin. Hata: {err}")
        return None
    except Exception as e:
        st.error(f"🔴 KRİTİK HATA: Veri işleme hatası. Veri formatınız yanlış olabilir. Hata: {e}")
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
    
else:
    st.warning("Veritabanında bu aboneye ait veri bulunamadı veya bağlantı kurulamadı.")


# --- TAHMİN BÖLÜMÜ ---

if veri_var_mi:
    try:
        # Yeni tahmin_yap fonksiyonunu çağırıyoruz
        gunluk_tahmin, haftalik_tahmin, aylik_tahmin = tahmin_yap(df)

        col1, col2, col3 = st.columns(3)

        if gunluk_tahmin > 0:
            col1.metric("Yarın Tahmini Tüketim", f"{gunluk_tahmin:.2f} Lt")
        else:
            col1.info("Yeterli veri yok (en az 7 gün).")
            
        col2.metric("Haftalık Tahmini Tüketim", f"{haftalik_tahmin:.2f} Lt")
        col3.metric("Aylık Tahmini Tüketim", f"{aylik_tahmin:.2f} Lt")
    
    except Exception as e:
        st.error(f"Tahmin hesaplanırken bir hata oluştu: {e}")
