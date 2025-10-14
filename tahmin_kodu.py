# Dosya Adı: tahmin_kodu.py
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

ROLLING_WINDOW = 7 

# ❗ DÜZENLEYİN: Bu aboneden veri çekeceğiz.
ABONE_ID = "ABONE_0001" 
KOLEKSIYON_ADI = 'su_okumalar' 
# ❗ DÜZENLEYİN: Service Account dosyasının adı
SERVICE_ACCOUNT_FILE = 'akillisutakip-firebase-adminsdk-fbsvc-3de4b6982e.json' 


# --- BAĞLANTIYI KUR ---
# Uygulama daha önce başlatılmamışsa başlat
# Dosya Adı: tahmin_kodu.py (GÜNCELLENMİŞ BULUT SÜRÜMÜ)
# ... (Diğer importlar)

# --- BAĞLANTIYI KUR (SECRETS ile) ---
if not firebase_admin._apps:
    try:
        # Streamlit Cloud'da çalışırken gizli anahtarı secrets objesinden alır
        cred = credentials.Certificate(st.secrets["firebase"]) 
        firebase_admin.initialize_app(cred)
    except Exception:
        # Loglama yapamayız, ancak Streamlit Cloud bu hatayı yakalayacaktır
        pass
        
# ... (Kodun geri kalanı aynı kalır)
        

def tahmin_yap(abone_id=ABONE_ID):
    
    # Eğer Firebase başlatılmadıysa (hatalı JSON dosyası vb.), tahmin yapma
    if not firebase_admin._apps:
        return 0.0, 0.0, 0.0
        
    db = firestore.client()
    
    try:
        # 1. Firestore'dan Veri Çekme (Sadece seçilen ABONE_ID için)
        docs = db.collection(KOLEKSIYON_ADI).where('abone_id', '==', abone_id).stream()
        
        # Veriyi DataFrame'e dönüştürme
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
