# Dosya Adı: su_tahmin.py (TEMİZ BULUT SÜRÜMÜ)
import streamlit as st
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from tahmin_kodu import tahmin_yap 
import os 

st.set_page_config(layout="wide")
st.title("💧 Akıllı Su Tüketimi İzleme ve Tahmin (Firebase)")

KOLEKSIYON_ADI = 'su_okumalar' 
ROLLING_WINDOW = 7 
ABONE_ID = "ABONE_0001" # Şimdilik sabit abone


# --- SADECE BURADA BAĞLANTI KURULUR (SECRETS ile) ---
# Dosya Adı: su_tahmin.py (YENİ ÇEVRESEL DEĞİŞKEN SÜRÜMÜ)
import streamlit as st
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os # YENİ EKLENDİ
from tahmin_kodu import tahmin_yap 

st.set_page_config(layout="wide")
st.title("💧 Akıllı Su Tüketimi İzleme ve Tahmin (Firebase)")

KOLEKSIYON_ADI = 'su_okumalar' 
ROLLING_WINDOW = 7 
ABONE_ID = "ABONE_0001" # Şimdilik sabit abone


# --- BAĞLANTIYI KUR (Çevresel Değişkenler ile) ---
if not firebase_admin._apps:
    try:
        # Çevresel değişkenlerden yapılandırma verisini okur
        # private_key'deki \n karakterlerini geri eklemeyi UNUTMAYIN (Çok Önemli!)
        firebase_config = {
            "type": os.environ["FIREBASE_TYPE"],
            "project_id": os.environ["FIREBASE_PROJECT_ID"],
            "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
            "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
            "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
            "client_id": os.environ["FIREBASE_CLIENT_ID"],
            "auth_uri": os.environ["FIREBASE_AUTH_URI"],
            "token_uri": os.environ["FIREBASE_TOKEN_URI"],
            "auth_provider_x509_cert_url": os.environ["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"],
            "client_x509_cert_url": os.environ["FIREBASE_CLIENT_X509_CERT_URL"],
            "universe_domain": os.environ["FIREBASE_UNIVERSE_DOMAIN"]
        }
        
        cred = credentials.Certificate(firebase_config) 
        firebase_admin.initialize_app(cred)
        
    except Exception:
        st.error("🔴 KRİTİK HATA: Firebase bağlantısı kurulamadı. Lütfen Streamlit Environment Variables ayarlarınızı kontrol edin.")
        st.stop()


# ... (Kodun geri kalanı aynı kalır)


# --- VERİ YÜKLEME VE GRAFİK OLUŞTURMA ---
db = firestore.client()
# Kalan kodunuz aynı kalır...
# ...

# --- VERİ YÜKLEME VE GRAFİK OLUŞTURMA ---
db = firestore.client()
veri_var_mi = False

# Kalan kodunuz aynı kalır...
try:
    # 1. Firestore'dan Veri Çekme
    docs = db.collection(KOLEKSIYON_ADI).where('abone_id', '==', ABONE_ID).stream()
    
    veri_listesi = []
    son_tarih = None
    # ... (Geri kalan kodunuz)
    for doc in docs:
        veri = doc.to_dict()
        veri_listesi.append({
            "tarih": datetime.strptime(veri["timestamp"], '%Y-%m-%d %H:%M:%S'),
            "tuketim": veri["tuketim"]
        })
        son_tarih = veri_listesi[-1]["tarih"]
        
    df = pd.DataFrame(veri_listesi)
    
    if not df.empty:
        veri_var_mi = True
        df = df.sort_values("tarih")
        
        # Günlük Tüketimi Hesapla
        df["gun"] = df["tarih"].dt.date
        gunluk = df.groupby("gun")["tuketim"].sum().reset_index()

        st.subheader(f"Günlük Su Tüketimi Grafiği ({ABONE_ID})")
        st.line_chart(gunluk.set_index("gun")["tuketim"], use_container_width=True)
        st.markdown(f"**Son Veri Zamanı:** {son_tarih.strftime('%d-%m-%Y %H:%M')}")
        
    else:
        st.warning("Veritabanında bu aboneye ait veri bulunamadı.")
        
except Exception:
    st.error("Firebase bağlantısında veya veri okumada kritik hata oluştu.")
    st.stop()


# --- TAHMİN BÖLÜMÜ ---
if veri_var_mi:
    gunluk_tahmin, haftalik_tahmin, aylik_tahmin = tahmin_yap(ABONE_ID)
    # ... (Geri kalan kodunuz)
    col1, col2, col3 = st.columns(3)

    if gunluk_tahmin > 0.0:
        
        st.success("✅ Tahmin Modeli Başarıyla Çalıştı!") 
        st.subheader("İleriye Yönelik Tüketim Tahminleri")

        col1.metric("👉 Tahmini Yarınki Tüketim", f"{gunluk_tahmin:.2f} m³")
        col2.metric("🗓️ Tahmini 7 Günlük Toplam", f"{haftalik_tahmin:.2f} m³")
        col3.metric("💰 Tahmini 1 Aylık Toplam Tüketim", f"{aylik_tahmin:.2f} m³")
        
    else:
        st.warning(f"⚠️ Tahmin yapmak için en az {ROLLING_WINDOW} günlük veri gerekiyor. Şu an {len(gunluk)} günlük veri var.")


