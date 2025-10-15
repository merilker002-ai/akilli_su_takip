# Dosya Adı: tahmin_kodu.py (TEMİZLENMİŞ SÜRÜM)
import pandas as pd
from datetime import datetime
import numpy as np
# Eski Firebase kütüphaneleri (firebase_admin, credentials, firestore, os) KALDIRILDI

ROLLING_WINDOW = 7 
# ABONE_ID, KOLEKSIYON_ADI, SERVICE_ACCOUNT_FILE kaldırıldı

# --- TAHMİN FONKSİYONU ---

def tahmin_yap(df):
    """
    Tüketim verisi DataFrame'ini alır (tarih ve tuketim sütunları olmalı) 
    ve hareketli ortalamaya dayalı tahminler yapar.
    """
    
    if df.empty or len(df["gun"].unique()) < ROLLING_WINDOW:
        # En az ROLLING_WINDOW (7) günlük veri yoksa
        return 0.0, 0.0, 0.0

    # 1. Günlük Toplam Tüketimi Hesapla
    # df["gun"] sütunu zaten su_tahmin.py'de oluşturuldu.
    gunluk = df.groupby("gun")["tuketim"].sum().reset_index()
    
    # 2. Hareketli Ortalama Hesaplama (Rolling Average)
    # Son 7 günlük ortalamayı bulur
    gunluk['rolling_avg'] = gunluk['tuketim'].rolling(window=ROLLING_WINDOW, min_periods=ROLLING_WINDOW).mean()
    
    # Son hareketli ortalama değeri (Tahmin için kullanacağımız temel)
    son_ort = gunluk['rolling_avg'].iloc[-1]
    
    # 3. Tahminleri Hesaplama
    
    # a) Yarınlık Tahmin (Son Hareketli Ortalama)
    gunluk_tahmin = son_ort
    
    # b) Haftalık Tahmin (7 günlük ortalama * 7 gün)
    haftalik_tahmin = son_ort * 7
    
    # c) Aylık Tahmin (7 günlük ortalama * 30 gün)
    aylik_tahmin = son_ort * 30
    
    return gunluk_tahmin, haftalik_tahmin, aylik_tahmin
