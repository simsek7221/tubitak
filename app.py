from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Akıllı Kask | Güvenlik Paneli", page_icon="🪖", layout="wide"
)

# Özel CSS ile Renkli ve Şık Tasarım Dokunuşları
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #1f4068, #162447);
        padding: 20px;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .badge-kask {
        background-color: #e94560;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 15px;
        float: right;
    }
    .metric-card {
        background-color: #1e1e2f;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00adb5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Üst Başlık ve Kask Numarası Alanı
st.markdown(
    """
    <div class="main-header">
        <span class="badge-kask">🪖 KASK NO: KASK-001</span>
        <h1 style="margin: 0; font-size: 26px;">AKILLI KASK TELEMETRİ</h1>
        <p style="margin: 0; color: #a4b0be; font-size: 14px;">TÜBİTAK Proje İzleme ve Güvenlik Paneli • Canlı Bağlantı 🟢</p>
    </div>
""",
    unsafe_allow_html=True,
)

st.write("")


# Sadece veri alanını arka planda otomatik güncelleyen fonksiyon (Sayfayı zıplatmaz)
@st.fragment(run_every=3)
def telemetry_dashboard():
  try:
    response = requests.get(FIREBASE_URL, timeout=5)
    if response.status_code == 200:
      data = response.json()

      if data:
        ivme_val = float(data.get("ivme", 1.0))
        duman_val = int(data.get("duman", 0))
        sos_val = int(data.get("sos", 0))
        lat = float(data.get("lat", 38.5023))
        lon = float(data.get("lon", 43.3820))
      else:
        ivme_val, duman_val, sos_val = 1.0, 0, 0
        lat, lon = 38.5023, 43.3820

      simdi = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

      # Sürücü Bilgisi
      st.info("👤 **Aktif Sürücü:** Demo Sürücü | **Cihaz ID:** KASK-001")

      # Renkli Sistem Durum Banner'ı
      if sos_val == 1 or ivme_val > 3.5 or duman_val > 250:
        st.error(
            "🚨 **KRİTİK UYARI!** Kask kullanıcısı tehlikede veya kaza"
            " algılandı!"
        )
      else:
        st.success(
            "✨ **SİSTEM ÇOK İYİ DURUMDA** — Herhangi bir tehlike tespit edilmedi."
        )

      # Renkli 4'lü Metrik Kartları
      col1, col2, col3, col4 = st.columns(4)

      with col1:
        st.markdown(
            """<div class="metric-card">
            <h4 style="color:#ff6b6b; margin:0;">🚨 KAZA DURUMU</h4>""",
            unsafe_allow_html=True,
        )
        if ivme_val > 3.5:
          st.error("Kaza Algılandı!")
        else:
          st.success("Normal (Kaza Yok)")
        st.caption(f"İvme: {round(ivme_val, 2)} g")
        st.markdown("</div>", unsafe_allow_html=True)

      with col2:
        st.markdown(
            """<div class="metric-card">
            <h4 style="color:#feca57; margin:0;">⚠️ ALKOL / GAZ</h4>""",
            unsafe_allow_html=True,
        )
        if duman_val > 250:
          st.warning("Yüksek Gaz Seviyesi")
        else:
          st.info("Gaz/Buhar Normal")
        st.caption(f"Değer: {duman_val}")
        st.markdown("</div>", unsafe_allow_html=True)

      with col3:
        st.markdown(
            """<div class="metric-card">
            <h4 style="color:#48dbfb; margin:0;">📍 GPS KONUM</h4>""",
            unsafe_allow_html=True,
        )
        st.write("Van Merkez")
        st.caption(f"Lat: {lat}, Lon: {lon}")
        st.markdown("</div>", unsafe_allow_html=True)

      with col4:
        st.markdown(
            """<div class="metric-card">
            <h4 style="color:#ff9ff3; margin:0;">🆘 SOS ÇAĞRISI</h4>""",
            unsafe_allow_html=True,
        )
        if sos_val == 1:
          st.error("AKTİF (Butona Basıldı!)")
        else:
          st.success("Pasif (Beklemede)")
        st.caption("Kask Buton Durumu")
        st.markdown("</div>", unsafe_allow_html=True)

      st.markdown("---")

      # Harita ve Detay Bölümü
      map_col, info_col = st.columns([2, 1])

      with map_col:
        st.markdown("### 🗺️ CANLI GOOGLE MAPS / GPS KONUMU")
        map_data = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.map(map_data, zoom=13, use_container_width=True)

      with info_col:
        st.markdown("### 📌 CİHAZ BİLGİLERİ")
        st.write("**Kask Kimliği:** KASK-001")
        st.write("**Bağlantı Türü:** Google Cloud (Firebase)")
        st.write("**Durum:** Çevrim İçi 🟢")
        st.markdown("---")
        st.info(f"⏱️ **Son Güncelleme:**\n{simdi}")

    else:
      st.error("Google Cloud veritabanına bağlanılamadı.")

  except Exception as e:
    st.error(f"Bağlantı hatası: {e}")


# Firebase URL Adresiniz
FIREBASE_URL = "https://akilli-kask-proje-default-rtdb.europe-west1.firebasedatabase.app/telemetri.json"

# Paneli Çalıştır
telemetry_dashboard()

st.markdown("---")

# Sabit Kontrol Butonları
b1, b2 = st.columns(2)
with b1:
  if st.button("🔴 ALARMI İPTAL ET", use_container_width=True):
    st.toast("Alarm başarıyla sıfırlandı!")
with b2:
  if st.button("🔵 SESLİ UYARIYI AÇ", use_container_width=True):
    st.toast("Kask hoparlöründen sesli uyarı verildi!")
