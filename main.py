import time
import pandas as pd
import requests
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Akıllı Kask Kontrol Paneli", page_icon="🪖", layout="centered"
)

st.title("🪖 TÜBİTAK Akıllı Kask Paneli")
st.write("ThingSpeak Bulut Üzerinden Canlı Veri ve Durum Takibi")

# ThingSpeak Kanal ID'nizi buraya yazın (Örn: "1234567")
CHANNEL_ID = "3558172"

# Arayüz Konteyneri
placeholder = st.empty()


def thingspeak_verilerini_al():
  try:
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results=1"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      data = response.json()
      feeds = data.get("feeds")
      if feeds:
        latest = feeds[0]
        return {
            "ivme": float(latest.get("field1", 0) or 0),
            "duman": int(float(latest.get("field2", 0) or 0)),
            "sos": int(float(latest.get("field3", 0) or 0)),
        }
  except Exception as e:
    return None
  return None


# Canlı Akış Döngüsü
while True:
  data = thingspeak_verilerini_al()

  with placeholder.container():
    if data:
      # Metrik Kartları
      col1, col2, col3 = st.columns(3)
      col1.metric("İvme (X)", f"{data['ivme']} g")
      col2.metric("Duman / Gaz", data["duman"])

      sos_durum_str = "BASILDI!" if data["sos"] == 1 else "YOK"
      col3.metric("SOS Durumu", sos_durum_str)

      # SOS Acil Durum Uyarısı
      if data["sos"] == 1:
        st.error(
            "🚨 KRİTİK UYARI: Kask kullanıcısı SOS butonuna bastı! Acil durum"
            " aktif!"
        )
      else:
        st.success("Sistem Durumu: Normal")

    else:
      st.warning(
          "Buluttan henüz veri alınamadı. Deneyap Kart'ın veri göndermesini"
          " bekliyor veya Channel ID'yi kontrol edin."
      )

  # ThingSpeak ücretsiz sürümü saniyede çok fazla istek istemez (15 saniye önerilir)
  time.sleep(15)
  st.rerun()
