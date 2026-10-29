import time
from datetime import datetime
import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Akıllı Kask | Güvenlik Paneli",
    page_icon="🪖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Session State Tanımlamaları
if "crash_start_time" not in st.session_state:
  st.session_state.crash_start_time = None
if "crash_cancelled" not in st.session_state:
  st.session_state.crash_cancelled = False
if "manual_alarm_stop" not in st.session_state:
  st.session_state.manual_alarm_stop = False

# Arayüz CSS (Görseldeki Parlaklık, Kontrast ve Renk Düzeni ile Birebir)
st.markdown(
    """
    <style>
    .stApp { 
        background-color: #0b0e14; 
        color: #d1d5db; 
    }
    .top-header {
        background: linear-gradient(90deg, #111622, #1a202c);
        padding: 14px 20px;
        border-radius: 8px;
        border: 1px solid #2d3748;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .driver-box {
        background-color: #111622;
        padding: 12px 20px;
        border-radius: 8px;
        border: 1px solid #2d3748;
        margin-bottom: 14px;
        font-weight: bold;
        color: #63b3ed;
    }
    .status-normal {
        background: linear-gradient(90deg, #133a27, #1c5236);
        color: #48bb78;
        padding: 14px;
        border-radius: 8px;
        font-size: 19px;
        font-weight: bold;
        text-align: center;
        border: 1px solid #38a169;
        margin-bottom: 14px;
    }
    .status-alert {
        background: linear-gradient(90deg, #63171b, #9b1c1c);
        color: #ffffff;
        padding: 14px;
        border-radius: 8px;
        font-size: 19px;
        font-weight: bold;
        text-align: center;
        border: 1px solid #e53e3e;
        margin-bottom: 14px;
    }
    .card-box {
        background-color: #111622;
        padding: 14px;
        border-radius: 8px;
        border: 1px solid #2d3748;
        height: 145px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .map-footer-banner {
        background-color: rgba(11, 14, 20, 0.85);
        color: #a0aec0;
        padding: 6px 10px;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 0.5px;
        border-bottom-left-radius: 6px;
        border-bottom-right-radius: 6px;
        border: 1px solid #2d3748;
        border-top: none;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Firebase Realtime Database URL
FIREBASE_URL = "https://akilli-kask-proje-default-rtdb.europe-west1.firebasedatabase.app/telemetri.json"


# Arka Planda Veri Yenileme (Fragment)
@st.fragment(run_every=3)
def render_dashboard():
  try:
    response = requests.get(FIREBASE_URL, timeout=5)
    if response.status_code == 200:
      data = response.json() or {}
    else:
      data = {}
  except:
    data = {}

  ivme_val = float(data.get("ivme", 1.0))
  duman_val = int(data.get("duman", 180))
  sos_val = int(data.get("sos", 0))

  # Tarayıcı/Cihaz Üzerinden Canlı GPS Konum Bilgisi
  location = streamlit_geolocation()
  if location.get("latitude") and location.get("longitude"):
    lat = float(location["latitude"])
    lon = float(location["longitude"])
    konum_baslik = "Konum Alındı"
    konum_alt_metin = "GPS koordinatı aktif."
    konum_kaynagi = "Canlı GPS Konumu"
  else:
    lat, lon = 38.5023, 43.3820  # Van Merkez (Görseldeki referans konum)
    konum_baslik = "Konum Alınıyor..."
    konum_alt_metin = "GPS modülünden konum bekleniyor."
    konum_kaynagi = "GPS konumu bekleniyor. Harita temsilidir."

  now_str = datetime.now().strftime("%d.%m.%Y   %H:%M:%S")

  # Kaza Algılama ve 15 Saniye Geri Sayım Mantığı
  is_crash_detected = ivme_val > 3.5
  if is_crash_detected and not st.session_state.crash_cancelled:
    if st.session_state.crash_start_time is None:
      st.session_state.crash_start_time = time.time()
  elif not is_crash_detected:
    st.session_state.crash_start_time = None
    st.session_state.crash_cancelled = False

  crash_active_final = False
  if (
      st.session_state.crash_start_time is not None
      and not st.session_state.crash_cancelled
  ):
    elapsed = int(time.time() - st.session_state.crash_start_time)
    remaining = 15 - elapsed
    if remaining > 0:
      st.warning(
          f"🚨 **KAZA TİTREŞİMİ ALGILANDI!** İptal edilmezse acil durum alarmı"
          f" çalacak: **{remaining} saniye** kaldı!"
      )
      if st.button(
          "🛡️ KAZAYI İPTAL ET (YANLIŞ ALARM)", use_container_width=True
      ):
        st.session_state.crash_cancelled = True
        st.session_state.crash_start_time = None
        st.rerun()
    else:
      crash_active_final = True

  # 1. Üst Başlık (Görseldeki IP ve Yapı ile Birebir)[span_1](start_span)[span_1](end_span)
  st.markdown(
      f"""
        <div class="top-header">
            <div>
                <h2 style="margin:0; color:#ffffff; font-size:21px;">🪖 AKILLI KASK <span style="font-size:12px; background:#e53e3e; color:white; padding:2px 8px; border-radius:10px; margin-left:6px; font-weight:normal;">KASK-001</span></h2>
                <p style="margin:2px 0 0 0; color:#a0aec0; font-size:12px;">Güvenli Sürüş, Güvenli Yarınlar</p>
            </div>
            <div style="text-align:right;">
                <span style="color:#a0aec0; font-size:12px;">📅 {now_str}</span><br>
                <span style="color:#48bb78; font-weight:bold; font-size:12px;">⚡ Bağlı • CANLI &nbsp;|&nbsp; 192.168.4.1</span>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # 2. Sürücü Bilgisi[span_2](start_span)[span_2](end_span)
  st.markdown(
      """
        <div class="driver-box">
            👤 SÜRÜCÜ &nbsp;&nbsp;&nbsp;&nbsp; <span style="color:#ffffff;">Demo Sürücü</span>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # 3. Sistem Durumu Banner[span_3](start_span)[span_3](end_span)
  alarm_durumu_aktif = (
      sos_val == 1 or crash_active_final or duman_val > 350
  ) and not st.session_state.manual_alarm_stop

  if alarm_durumu_aktif:
    st.markdown(
        """
            <div class="status-alert">
                🚨 SESLİ ALARMI AÇ — Acil Durum Veya Kaza Algılandı!
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <audio autoplay loop>
          <source src="https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg" type="audio/ogg">
        </audio>
        """,
        unsafe_allow_html=True,
    )
  else:
    st.markdown(
        """
            <div class="status-normal">
                ✔ SİSTEM NORMAL
                <div style="font-size:12px; font-weight:normal; color:#a0aec0; margin-top:2px;">Aktif alarm yok</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  # 4. 4'lü Metrik Kartları (Görseldeki Yazılarla Birebir Uyumlu)[span_4](start_span)[span_4](end_span)
  c1, c2, c3, c4 = st.columns(4)

  with c1:
    kaza_txt = "Kaza Var" if is_crash_detected else "Kaza Yok"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #f56565;">
                <div><span style="font-size:16px;">🚨</span> <b>KAZA DURUMU</b></div>
                <div style="font-size:17px; font-weight:bold; color:{'#f56565' if is_crash_detected else '#ffffff'};">{kaza_txt}</div>
                <div style="font-size:11px; color:#a0aec0;">Kaza sayısı: 0</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c2:
    gaz_txt = "Yüksek Gaz" if duman_val > 350 else "Gaz/Buhar Yok"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #ecc94b;">
                <div><span style="font-size:16px;">⚠️</span> <b>ALKOL / BUHAR UYARISI</b></div>
                <div style="font-size:17px; font-weight:bold; color:{'#ecc94b' if duman_val > 350 else '#ffffff'};">{gaz_txt}</div>
                <div style="font-size:10px; color:#a0aec0; line-height:1.2;">Gaz/buhar sensörüyle uyarı takibi; promil ölçümü değildir.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c3:
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #4299e1;">
                <div><span style="font-size:16px;">📍</span> <b>KONUM BİLGİSİ</b></div>
                <div style="font-size:15px; font-weight:bold; color:#ffffff;">{konum_baslik}</div>
                <div style="font-size:10px; color:#a0aec0; line-height:1.2;">{konum_alt_metin}<br>GPS koordinatı bekleniyor</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c4:
    sos_txt = "AKTİF" if sos_val == 1 else "Pasif"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #f56565;">
                <div><span style="font-size:16px;">🆘</span> <b>SOS YARDIM ÇAĞRISI</b></div>
                <div style="font-size:17px; font-weight:bold; color:{'#f56565' if sos_val == 1 else '#ffffff'};">{sos_txt}</div>
                <div style="font-size:11px; color:#a0aec0;">Kask üzerindeki butonla kontrol edilir.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  st.write("")

  # Kontrol Butonları[span_5](start_span)[span_5](end_span)
  b_col1, b_col2 = st.columns(2)
  with b_col1:
    if st.button("🚨 ALARMI İPTAL ET", use_container_width=True):
      st.session_state.manual_alarm_stop = True
      st.session_state.crash_cancelled = True
      st.toast("Alarm iptal edildi!")
  with b_col2:
    if st.button("🔊 SESLİ ALARMI AÇ", use_container_width=True):
      st.session_state.manual_alarm_stop = False
      st.toast("Sesli alarm modu açıldı.")

  st.markdown("---")

  # Harita ve Yan Bilgi Paneli (Görseldeki düzenle birebir)[span_6](start_span)[span_6](end_span)
  map_col, info_col = st.columns([2.2, 1])

  with map_col:
    st.markdown("### 🗺️ KONUM HARİTASI")

    # Folium Haritası Oluşturma (Görseldeki Leaflet/Uydu Görünümü)
    m = folium.Map(
        location=[lat, lon],
        zoom_start=14,
        tiles=None,
        control_scale=True,
    )

    # Esri World Imagery (Renkli Yüksek Çözünürlüklü Uydu Katmanı)
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri",
        name="Uydu Görünümü",
    ).add_to(m)

    # Kırmızı İşaretçi (Pin) ve Pop-up
    folium.Marker(
        [lat, lon],
        popup="KASK-001 (Canlı GPS)",
        tooltip="KASK-001",
        icon=folium.Icon(color="red", icon="shield", prefix="fa"),
    ).add_to(m)

    # Haritayı Streamlit İçinde Göster
    st_folium(m, height=390, use_container_width=True)

    # Görselin altındaki uyarı bandı
    st.markdown(
        """
        <div class="map-footer-banner">
            VAN MERKEZ • CANLI GPS TAKİBİ AKTİF
        </div>
    """,
        unsafe_allow_html=True,
    )

  with info_col:
    st.markdown("### 📍 KONUM BİLGİSİ")
    st.write("**Mevcut Konum:**")
    st.write("**Van, Türkiye (Canlı)**")
    st.caption(konum_kaynagi)
    st.markdown("---")
    st.write(f"**Son güncelleme:**\n{now_str}")
    st.write("**Cihaz ID:** KASK-001")
    st.write("**Sistem Durumu:** Çevrim İçi 🟢")


# Paneli Çalıştır
render_dashboard()
