import time
import requests
import streamlit as st

st.set_page_config(
    page_title="Akıllı Kask Kontrol Paneli", page_icon="🪖", layout="centered"
)

st.title("🪖 TÜBİTAK Akıllı Kask Paneli")
st.write("Google Cloud (Firebase) Üzerinden Canlı Takip")

# Firebase Realtime Database URL Adresin
FIREBASE_URL = "https://akilli-kask-proje-default-rtdb.europe-west1.firebasedatabase.app/telemetri.json"

placeholder = st.empty()

while True:
  try:
    response = requests.get(FIREBASE_URL, timeout=5)
    if response.status_code == 200:
      data = response.json()

      with placeholder.container():
        if data:
          ivme_val = float(data.get("ivme", 0))
          duman_val = int(data.get("duman", 0))
          sos_val = int(data.get("sos", 0))

          col1, col2, col3 = st.columns(3)
          col1.metric("İvme (X)", f"{ivme_val} g")
          col2.metric("Duman / Gaz", duman_val)

          sos_durum_str = "BASILDI!" if sos_val == 1 else "YOK"
          col3.metric("SOS Durumu", sos_durum_str)

          if sos_val == 1:
            st.error(
                "🚨 KRİTİK UYARI: Kask kullanıcısı SOS butonuna bastı! Acil"
                " durum aktif!"
            )
          else:
            st.success("Sistem Durumu: Çevrim İçi ve Normal")
        else:
          st.warning(
              "Bulut veritabanında henüz veri yok. Deneyap Kart'ın veri"
              " gönderdiğinden emin olun."
          )
    else:
      st.error("Google Cloud veritabanına erişilemedi.")
  except Exception as e:
    st.error(f"Bağlantı hatası: {e}")

  time.sleep(3)
  st.rerun()
