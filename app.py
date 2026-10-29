import time
from datetime import datetime
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from streamlit_geolocation import streamlit_geolocation

# Sayfa Yapılandırması (Görseldeki tam genişlik ve koyu tema için)
st.set_page_config(
    page_title="Akıllı Kask | Güvenlik Paneli",
    page_icon="🪖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Session State Tanımlamaları (Alarm & Kaza Mantığı)
if "crash_start_time" not in st.session_state:
  st.session_state.crash_start_time = None
if "crash_cancelled" not in st.session_state:
  st.session_state.crash_cancelled = False
if "manual_alarm_stop" not in st.session_state:
  st.session_state.manual_alarm_stop = False

# Arayüz CSS (2367.jpg Görselindeki Parlaklık, Kontrast ve Renk Paletinin Birebir Kopyası)
st.markdown(
    """
    <style>
    /* Arka Plan ve Genel Renk Dengesi */
    .stApp { 
        background-color: #0b0e14; 
        color: #d1d5db; 
    }
    
    /* Üst Başlık Şeridi */
    .top-header {
        background: linear-gradient(90deg, #111622, #1a202c);
        padding: 16px 22px;
        border-radius: 10px;
        border: 1px solid #2d3748;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    
    /* Sürücü Bilgi Kutusu */
    .driver-box {
        background-color: #111622;
        padding: 14px 22px;
        border-radius: 10px;
        border: 1px solid #2d3748;
        margin-bottom: 16px;
        font-weight: bold;
        color: #63b3ed;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }
    
    /* Sistem Normal Banner'ı (Yeşil Parlaklık) */
    .status-normal {
        background: linear-gradient(90deg, #133a27, #1c5236);
        color: #48bb78;
        padding: 16px;
        border-radius: 10px;
        font-size: 21px;
        font-weight: bold;
        text-align: center;
        border: 1px solid #38a169;
        margin-bottom: 16px;
        box-shadow: 0 0 15px rgba(56, 161, 105, 0.2);
    }
    
    /* Sistem Alarm Banner'ı (Kırmızı Parlaklık) */
    .status-alert {
        background: linear-gradient(90deg, #63171b, #9b1c1c);
        color: #ffffff;
        padding: 16px;
        border-radius: 10px;
        font-size: 21px;
        font-weight: bold;
        text-align: center;
        border: 1px solid #e53e3e;
        margin-bottom: 16px;
        box-shadow: 0 0 20px rgba(229, 62, 62, 0.4);
    }
    
    /* Metrik Kartları (Parlak Kenarlıklar ve İç Metinler) */
    .card-box {
        background-color: #111622;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #2d3748;
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
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

  # Konum Bilgisi (Sistemde "GPS Konumu" Olarak Görünecektir)
  location = streamlit_geolocation()
  if location.get("latitude") and location.get("longitude"):
    lat = float(location["latitude"])
    lon = float(location["longitude"])
    konum_durum_metni = "GPS Koordinatı Aktif"
    konum_kaynagi = "Canlı GPS Konumu"
  else:
    lat, lon = 38.5023, 43.3820  # Van Merkez Varsayılan
    konum_durum_metni = "GPS modülünden konum bekleniyor."
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

  # 1. Üst Başlık (IP Adresi ve Başlık Görseldeki Gibidir)
  st.markdown(
      f"""
        <div class="top-header">
            <div>
                <h2 style="margin:0; color:#ffffff; font-size:22px; letter-spacing:0.5px;">🪖 AKILLI KASK <span style="font-size:13px; background:#e53e3e; color:white; padding:3px 10px; border-radius:12px; margin-left:8px; font-weight:normal;">KASK-001</span></h2>
                <p style="margin:3px 0 0 0; color:#a0aec0; font-size:13px;">Güvenli Sürüş, Güvenli Yarınlar</p>
            </div>
            <div style="text-align:right;">
                <span style="color:#a0aec0; font-size:13px;">📅 {now_str}</span><br>
                <span style="color:#48bb78; font-weight:bold; font-size:13px;">⚡ Bağlı • CANLI &nbsp;|&nbsp; 192.168.4.1</span>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # 2. Sürücü Bilgisi
  st.markdown(
      """
        <div class="driver-box">
            👤 SÜRÜCÜ &nbsp;&nbsp;&nbsp;&nbsp; <span style="color:#ffffff;">Demo Sürücü</span>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # 3. Sistem Durumu
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
                <div style="font-size:13px; font-weight:normal; color:#a0aec0; margin-top:2px;">Aktif alarm yok</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  # 4. 4'lü Metrik Kartları (Görseldeki Birebir Metinler ve Çizgiler)
  c1, c2, c3, c4 = st.columns(4)

  with c1:
    kaza_txt = "Kaza Var" if is_crash_detected else "Kaza Yok"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #f56565;">
                <div><span style="font-size:18px;">🚨</span> <b>KAZA DURUMU</b></div>
                <div style="font-size:18px; font-weight:bold; color:{'#f56565' if is_crash_detected else '#ffffff'};">{kaza_txt}</div>
                <div style="font-size:12px; color:#a0aec0;">Kaza sayısı: 0</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c2:
    gaz_txt = "Yüksek Gaz" if duman_val > 350 else "Gaz/Buhar Yok"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #ecc94b;">
                <div><span style="font-size:18px;">⚠️</span> <b>ALKOL / BUHAR UYARISI</b></div>
                <div style="font-size:18px; font-weight:bold; color:{'#ecc94b' if duman_val > 350 else '#ffffff'};">{gaz_txt}</div>
                <div style="font-size:11px; color:#a0aec0; line-height:1.2;">Gaz/buhar sensörüyle uyarı takibi; promil ölçümü değildir.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c3:
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #4299e1;">
                <div><span style="font-size:18px;">📍</span> <b>KONUM BİLGİSİ</b></div>
                <div style="font-size:16px; font-weight:bold; color:#ffffff;">{konum_durum_metni}</div>
                <div style="font-size:11px; color:#a0aec0;">GPS modülünden konum bekleniyor.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c4:
    sos_txt = "AKTİF" if sos_val == 1 else "Pasif"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #f56565;">
                <div><span style="font-size:18px;">🆘</span> <b>SOS YARDIM ÇAĞRISI</b></div>
                <div style="font-size:18px; font-weight:bold; color:{'#f56565' if sos_val == 1 else '#ffffff'};">{sos_txt}</div>
                <div style="font-size:12px; color:#a0aec0;">Kask üzerindeki butonla kontrol edilir.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  st.write("")

  # Control Butonları
  b_col1, b_col2 = st.columns(2)
  with b_col1:
    if st.button("🚨 ALARMI İPTAL ET", use_container_width=True):
      st.session_state.manual_alarm_stop = True
      st.session_state.crash_cancelled = True
      st.toast("Alarm sıfırlandı!")
  with b_col2:
    if st.button("🔊 SESLİ ALARMI AÇ", use_container_width=True):
      st.session_state.manual_alarm_stop = False
      st.toast("Sesli alarm modu aktif.")

  st.markdown("---")

  # Harita ve Yan Bilgi Paneli
  map_col, info_col = st.columns([2.2, 1])

  with map_col:
    st.markdown("### 🗺️ KONUM HARİTASI (GPS Canlı Takip)")

    df_map = pd.DataFrame(
        {
            "lat": [lat],
            "lon": [lon],
            "icon_data": [
                {
                    "url": (
                        "https://cdn-icons-png.flaticon.com/512/2965/2965352.png"
                    ),
                    "width": 128,
                    "height": 128,
                    "anchorX": 64,
                    "anchorY": 64,
                }
            ],
        }
    )

    # Renkli ESRI World Imagery Canlı Uydu Katmanı
    tile_layer = pdk.Layer(
        "TileLayer",
        data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        min_zoom=0,
        max_zoom=19,
        tileSize=256,
    )

    # Parlayan Neon Çember Katmanı
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        df_map,
        get_position="[lon, lat]",
        get_color=[229, 62, 62, 200],
        get_radius=80,
        radius_scale=6,
        radius_min_pixels=14,
        radius_max_pixels=45,
        get_line_color=[255, 255, 255, 230],
        get_line_width=3,
        pickable=True,
    )

    # Tam Merkezlenmiş Kask Görseli Katmanı
    icon_layer = pdk.Layer(
        "IconLayer",
        df_map,
        get_position="[lon, lat]",
        get_icon="icon_data",
        get_size=46,
        size_scale=1,
        pickable=True,
    )

    # Kask ID Rozet Katmanı
    text_layer = pdk.Layer(
        "TextLayer",
        df_map,
        get_position="[lon, lat]",
        get_text="'🛡️ KASK-001'",
        get_size=16,
        get_color=[255, 255, 255],
        get_background_color=[11, 22, 34, 230],
        get_alignment_baseline="'bottom'",
        get_pixel_offset=[0, -32],
    )

    view_state = pdk.ViewState(
        latitude=lat, longitude=lon, zoom=15, pitch=45, bearing=0
    )

    r = pdk.Deck(
        layers=[tile_layer, scatterplot_layer, icon_layer, text_layer],
        initial_view_state=view_state,
        map_style=None,
        tooltip={"text": "Cihaz: KASK-001\nEnlem: {lat}\nBoylam: {lon}"},
    )

    st.pydeck_chart(r, use_container_width=True)

  with info_col:
    st.markdown("### 📍 KONUM BİLGİSİ")
    st.write("**Mevcut Konum:**")
    st.write("**Van, Türkiye (örnek)**")
    st.caption(konum_kaynagi)
    st.markdown("---")
    st.write(f"**Son güncelleme:**\n{now_str}")
    st.write("**Cihaz ID:** KASK-001")
    st.write("**Sistem Durumu:** Çevrim İçi 🟢")


# Paneli Çalıştır
render_dashboard()
