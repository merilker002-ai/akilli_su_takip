# Dosya Adı: tahmin_kodu.py (REST API ile UYUMLU SÜRÜM)
import pandas as pd
from datetime import datetime, timedelta

# Ana uygulamadan gelen değişkenler
ROLLING_WINDOW = 7 

def tahmin_yap(df):
    """
    Verilen DataFrame'den (günlük veya toplam) hareketli ortalama yöntemini kullanarak
    bir sonraki gün, hafta ve ay için su tüketimi tahminleri yapar.
    
    Args:
        df (pd.DataFrame): 'tarih' ve 'tuketim' sütunlarını içeren tüm ham veriyi içerir.
        
    Returns:
        tuple: (gunluk_tahmin, haftalik_tahmin, aylik_tahmin)
    """
    
    if df.empty:
        return 0.0, 0.0, 0.0

    # 1. GÜNLÜK TOPLAM TÜKETİMİ HESAPLA
    df["gun"] = df["tarih"].dt.date
    gunluk = df.groupby("gun")["tuketim"].sum().reset_index()
    gunluk.columns = ['tarih', 'gunluk_tuketim']
    
    # 2. YETERLİ VERİ KONTROLÜ
    # Tahmin için en az ROLLING_WINDOW (7 gün) kadar veri olmalıdır.
    if len(gunluk) < ROLLING_WINDOW:
        # Yeterli veri yoksa sıfır döndür (su_tahmin.py bu durumu kontrol eder)
        return 0.0, 0.0, 0.0

    # 3. HAREKETLİ ORTALAMA HESAPLAMA
    # Son 7 günün ortalamasını alarak temel tahmin değerini buluruz.
    # .iloc[-1] son ortalamayı verir.
    ortalama_gunluk_tuketim = gunluk['gunluk_tuketim'].tail(ROLLING_WINDOW).mean()

    # 4. TAHMİNLERİ YAPMA
    
    # a) Yarın Tahmini (Bir sonraki gün)
    gunluk_tahmin = ortalama_gunluk_tuketim
    
    # b) Haftalık Tahmin (Önümüzdeki 7 günün toplamı)
    # Basit bir model: Son 7 gün ortalamasını 7 ile çarp.
    haftalik_tahmin = ortalama_gunluk_tuketim * 7
    
    # c) Aylık Tahmin (Önümüzdeki 30 günün toplamı)
    # Basit bir model: Son 7 gün ortalamasını 30 ile çarp.
    aylik_tahmin = ortalama_gunluk_tuketim * 30
    
    return gunluk_tahmin, haftalik_tahmin, aylik_tahmin
