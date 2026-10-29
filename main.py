import time
import pandas as pd
import requests
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Akıllı Kask Kontrol Paneli", page_icon="🪖", layout="centered"
)

st.title("🪖 TÜBİTAK Akıllı Kask Paneli")
st.write(
    "Deneyap Kart V2 üzerinden gelen anlık veriler ve canlı GPS harita"
    " takibi."
)

# Kartımızın tarayıcıda doğruladığımız gerçek IP adresi
ESP32_IP = "192.168.1.187"

# Arayüz Konteyneri
placeholder = st.empty()


def verileri_al():
  try:
    response = requests.get(f"http://{ESP32_IP}/veri", timeout=2)
    if response.status_code == 200:
      return response.json()
  except:
    return None
  return None


# Canlı Akış Döngüsü
while True:
  data = verileri_al()

  with placeholder.container():
    if data:
      # Metrik Kartları
      col1, col2, col3 = st.columns(3)
      col1.metric("İvme (X)", f"{data['ivme']} g")
      col2.metric("Sensör", data["sensor"])
      col3.metric("Kaza Durumu", data["kaza"])

      col4, col5, col6 = st.columns(3)
      col4.metric("SOS Durumu", data["sos"])
      col5.metric("Duman / Gaz", data["duman"])
      col6.metric("Eşik", data["esik"])

      # SOS Acil Durum Uyarısı
      if data["sos"] == "BASILDI!":
        st.error(
            "🚨 KRİTİK UYARI: Kask kullanıcısı SOS butonuna bastı! Acil durum"
            " aktif!"
        )

      # Streamlit Yerleşik Gerçek Harita Bileşeni (GPS)
      st.subheader("📍 Canlı GPS Konum Haritası")
      df_map = pd.DataFrame(
          [[data["lat"], data["lng"]]], columns=["lat", "lon"]
      )
      st.map(df_map, zoom=15)

    else:
      st.warning(
          f"Karttan veri alınamadı! Lütfen ESP32 IP adresini ({ESP32_IP}) ve"
          " Wi-Fi bağlantısını kontrol edin."
      )

  time.sleep(2)
  st.rerun()
