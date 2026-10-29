from datetime import datetime
import time
import pandas as pd
import requests
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Akıllı Kask | Güvenlik Paneli", page_icon="🪖", layout="wide"
)

# Firebase Realtime Database URL Adresin
FIREBASE_URL = "https://akilli-kask-proje-default-rtdb.europe-west1.firebasedatabase.app/telemetri.json"

# Üst Başlık Alanı
st.markdown(
    """
    <div style="background-color: #0e1117; padding: 10px; border-radius: 5px; border-bottom: 2px solid #262730;">
        <h2 style="color: white; margin: 0;">🪖 AKILLI KASK <span style="font-size: 16px; color: #808495; float: right;">📅 Bağlı • CANLI 🟢</span></h2>
        <p style="color: #808495; margin: 0; font-size: 14px;">Güvenli Sürüş, Güvenli Yarınlar</p>
    </div>
""",
    unsafe_allow_html=True,
)

st.write("")

placeholder = st.empty()

while True:
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

      with placeholder.container():
        # Sürücü Bilgisi
        st.info("👤 **SÜRÜCÜ:** Demo Sürücü (Aktif Oturum)")

        # Sistem Durum Banner'ı
        if sos_val == 1 or ivme_val > 3.5 or duman_val > 250:
          st.error(
              "🚨 **SİSTEM ALARMI AKTİF!** Kaza, aşırı duman veya acil durum"
              " algılandı!"
          )
        else:
          st.success("🟢 **SİSTEM NORMAL** — Aktif alarm yok, sürüş güvenli.")

        # 4'lü Metrik Kartları
        col1, col2, col3, col4 = st.columns(4)

        with col1:
          st.markdown("### 🚨 KAZA DURUMU")
          kaza_durum = (
              "Kaza Var!" if ivme_val > 3.5 else "Kaza Yok (Normal)"
          )
          st.write(kaza_durum)
          st.caption("İvme Değeri: " + str(round(ivme_val, 2)) + " g")

        with col2:
          st.markdown("### ⚠️ ALKOL / BUHAR")
          gaz_durum = "Yüksek Gaz!" if duman_val > 250 else "Gaz/Buhar Yok"
          st.write(gaz_durum)
          st.caption("Sensör Ölçüm: " + str(duman_val))

        with col3:
          st.markdown("### 📍 KONUM BİLGİSİ")
          st.write("Van, Türkiye (GPS)")
          st.caption(f"Lat: {lat}, Lon: {lon}")

        with col4:
          st.markdown("### 🆘 SOS ÇAĞRISI")
          sos_str = "AKTİF (BASILDI!)" if sos_val == 1 else "Pasif (Normal)"
          st.write(sos_str)
          st.caption("Kask üzerindeki buton")

        st.markdown("---")

        # Kontrol Butonları Satırı
        b1, b2 = st.columns(2)
        with b1:
          if st.button("🔴 ALARMI İPTAL ET", use_container_width=True):
            st.toast("Alarm sıfırlandı.")
        with b2:
          if st.button("🔵 SESLİ ALARMI AÇ", use_container_width=True):
            st.toast("Kask buzzer aktif edildi.")

        st.markdown("---")

        # Alt Bölüm: Google Maps Haritası ve Detay Bilgi
        map_col, info_col = st.columns([2, 1])

        with map_col:
          st.markdown("### 🗺️ KONUM HARİTASI (Google Maps / GPS)")
          # Streamlit harita bileşeni (Google Maps altyapısını simüle eder)
          map_data = pd.DataFrame({"lat": [lat], "lon": [lon]})
          st.map(map_data, zoom=13, use_container_width=True)

        with info_col:
          st.markdown("### 📌 KONUM DETAYI")
          st.write("**Mevcut Konum:**")
          st.write("Van Merkez, Türkiye")
          st.caption(
              "GPS uydularından ve Google Cloud üzerinden anlık konum"
              " izlenmektedir."
          )
          st.markdown("---")
          st.write(f"**Son Güncelleme:**\n{simdi}")

    else:
      st.error("Google Cloud veritabanına bağlanılamadı.")

  except Exception as e:
    st.error(f"Bağlantı hatası: {e}")

  time.sleep(3)
  st.rerun()
