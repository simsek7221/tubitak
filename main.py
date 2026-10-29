from datetime import datetime, timezone
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

# ThingSpeak Kanal ID'niz
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
            "created_at": latest.get("created_at"),  # Verinin gönderildiği zaman
        }
  except Exception as e:
    return None
  return None


# Canlı Akış Döngüsü
while True:
  data = thingspeak_verilerini_al()

  with placeholder.container():
    if data and data["created_at"]:
      # --- KARTIN AÇIK/KAPALI OLDUĞUNU KONTROL ET ---
      try:
        # ThingSpeak zaman damgasını UTC olarak al ve şimdiki zamanla kıyasla
        dt_str = data["created_at"].replace("Z", "+00:00")
        data_time = datetime.fromisoformat(dt_str)
        simdi = datetime.now(timezone.utc)
        fark_saniye = (simdi - data_time).total_seconds()
      except:
        fark_saniye = 0

      # Eğer son veri 40 saniyeden eskiyse, Deneyap Kart kapalı/çevrimdışı demektir
      if fark_saniye > 40:
        st.error(
            "⚠️ **CİHAZ ÇEVRİMDIŞI (OFFLINE)**: Deneyap Kart'ın enerjisi"
            f" kesik veya internet bağlantısı yok! (Son veri {int(fark_saniye)}"
            " saniye önce alındı)"
        )
      else:
        # Metrik Kartları (Sistem aktifse gösterilir)
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
          st.success("Sistem Durumu: Çevrim İçi ve Normal")

    else:
      st.warning(
          "Buluttan henüz veri alınamadı veya kanal boş. Deneyap Kart'ın veri"
          " gönderdiğinden emin olun."
      )

  # 10 saniyede bir sayfayı yenile
  time.sleep(10)
  st.rerun()
