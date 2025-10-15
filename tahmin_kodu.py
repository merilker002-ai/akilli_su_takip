# Dosya Adı: tahmin_kodu.py (GÜNCELLENMİŞ VE ST.SECRETS'I KALDIRILMIŞ SÜRÜM)
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
# import streamlit as st # ARTIK GEREKSİZ, KALDIRILDI

ROLLING_WINDOW = 7 
ABONE_ID = "ABONE_0001" 
KOLEKSIYON_ADI = 'su_okumalar' 


# --- BAĞLANTIYI KUR (st objesi DIŞARIDAN GELİR) ---
# Bu kodun artık tahmin_kodu.py'da olmaması gerekiyor. 
# Bağlantı, sadece su_tahmin.py'da bir kez yapılmalıdır.


def tahmin_yap(abone_id=ABONE_ID):
    # Fonksiyon, uygulamanın zaten başarılı bir şekilde Firebase'e bağlandığını varsayar.
    
    # Hata yakalama için sadece firebase_admin.apps kontrolü yeterli.
    if not firebase_admin._apps:
        # Bu durumda bir hata oluştuğunu varsayarız.
        return 0.0, 0.0, 0.0
        
    db = firestore.client()
    
    # Kalan kodunuz aynı kalır...
    try:
        # 1. Firestore'dan Veri Çekme (Sadece seçilen ABONE_ID için)
        docs = db.collection(KOLEKSIYON_ADI).where('abone_id', '==', abone_id).stream()
        
        # ... (Geri kalan kodunuz)
        veri_listesi = []
        for doc in docs:
            veri = doc.to_dict()
            veri_listesi.append({
                "tarih": datetime.strptime(veri["timestamp"], '%Y-%m-%d %H:%M:%S'),
                "tuketim": veri["tuketim"]
            })

        df = pd.DataFrame(veri_listesi)
        df = df.sort_values("tarih")
    
        # 2. Günlük Toplam Tüketimi Hesapla
        df["gun"] = df["tarih"].dt.date
        gunluk = df.groupby("gun")["tuketim"].sum().reset_index()

    except Exception:
        return 0.0, 0.0, 0.0

    # 3. Yeterli Gün Kontrolü
    if len(gunluk) < ROLLING_WINDOW:
        return 0.0, 0.0, 0.0

    # 4. Tahminleri Yap
    son_7_gun_ortalama = gunluk["tuketim"].tail(ROLLING_WINDOW).mean()
    gunluk_tahmin = son_7_gun_ortalama 
    haftalik_tahmin = son_7_gun_ortalama * 7
    aylik_tahmin = son_7_gun_ortalama * 30

    return gunluk_tahmin, haftalik_tahmin, aylik_tahmin
