from datetime import datetime, timezone
import time
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Akıllı Kask Kontrol Paneli", page_icon="🪖", layout="centered"
)

st.title("🪖 TÜBİTAK Akıllı Kask Paneli")
st.write("Adafruit IO Üzerinden Gerçek Zamanlı Canlı Takip")

AIO_USERNAME = "ismail7221"
AIO_KEY = "aio_sCFu71Nf0kVu0JtMC04obeJJvCVz"

headers = {"X-AIO-Key": AIO_KEY}
placeholder = st.empty()


def adafruit_verilerini_cek(feed_key):
  try:
    url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed_key}/data/last"
    response = requests.get(url, headers=headers, timeout=5)
    if response.status_code == 200:
      return response.json()
  except:
    return None
  return None


while True:
  ivme_data = adafruit_verilerini_cek("ivme")
  duman_data = adafruit_verilerini_cek("duman")
  sos_data = adafruit_verilerini_cek("sos")

  with placeholder.container():
    if ivme_data and "created_at" in ivme_data:
      try:
        veri_zamani = pd.to_datetime(ivme_data["created_at"])
        simdiki_zaman = pd.Timestamp.now(tz="UTC")
        fark_saniye = (simdiki_zaman - veri_zamani).total_seconds()
      except:
        fark_saniye = 0

      if fark_saniye > 15:
        st.error(
            "⚠️ **CİHAZ ÇEVRİMDIŞI (OFFLINE)**: Deneyap Kart kapalı veya"
            f" internet bağlantısı yok! (Son veri {int(fark_saniye)} saniye"
            " önce alındı)"
        )
      else:
        ivme_val = float(ivme_data.get("value", 0))
        duman_val = int(float(duman_data.get("value", 0) if duman_data else 0))
        sos_val = int(float(sos_data.get("value", 0) if sos_data else 0))

        col1, col2, col3 = st.columns(3)
        col1.metric("İvme (X)", f"{ivme_val} g")
        col2.metric("Duman / Gaz", duman_val)

        sos_durum_str = "BASILDI!" if sos_val == 1 else "YOK"
        col3.metric("SOS Durumu", sos_durum_str)

        if sos_val == 1:
          st.error(
              "🚨 KRİTİK UYARI: Kask kullanıcısı SOS butonuna bastı! Acil durum"
              " aktif!"
          )
        else:
          st.success("Sistem Durumu: Çevrim İçi ve Normal")
    else:
      st.warning(
          "Buluttan henüz veri alınamadı. Deneyap Kart'ın veri gönderdiğinden"
          " emin olun."
      )

  time.sleep(3)
  st.rerun()
