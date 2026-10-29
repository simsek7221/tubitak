import time
from datetime import datetime
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
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

# Arayüz Tasarım Stilleri (CSS)
st.markdown(
    """
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .top-header {
        background: linear-gradient(90deg, #161b22, #1f242d);
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid #30363d;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .driver-box {
        background-color: #161b22;
        padding: 12px 20px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 15px;
        font-weight: bold;
        color: #58a6ff;
    }
    .status-normal {
        background: linear-gradient(90deg, #1b4332, #2d6a4f);
        color: #52b788;
        padding: 15px;
        border-radius: 8px;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        border: 1px solid #52b788;
        margin-bottom: 15px;
    }
    .status-alert {
        background: linear-gradient(90deg, #780000, #c1121f);
        color: #fff;
        padding: 15px;
        border-radius: 8px;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        border: 1px solid #ff4d4d;
        margin-bottom: 15px;
    }
    .card-box {
        background-color: #161b22;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Firebase Realtime Database URL Adresin
FIREBASE_URL = "https://akilli-kask-proje-default-rtdb.europe-west1.firebasedatabase.app/telemetri.json"


# Arka planda verileri güncelleyen akıllı fonksiyon
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

  # Tabletin / Tarayıcının Gerçek Konum Bilgisini Alıyoruz
  location = streamlit_geolocation()
  if location.get("latitude") and location.get("longitude"):
    lat = float(location["latitude"])
    lon = float(location["longitude"])
    konum_kaynagi = "Tablet / Cihaz Canlı Konum"
  else:
    # Konum izni verilmediyse varsayılan konum (Van Merkez)
    lat, lon = 38.5023, 43.3820
    konum_kaynagi = "Varsayılan Konum (İzin Bekleniyor)"

  now_str = datetime.now().strftime("%d.%m.%Y   %H:%M:%S")

  # Kaza Algılama Kontrolü ve 15 Saniye Geri Sayım Mantığı
  is_crash_detected = ivme_val > 3.5
  if is_crash_detected and not st.session_state.crash_cancelled:
    if st.session_state.crash_start_time is None:
      st.session_state.crash_start_time = time.time()
  elif not is_crash_detected:
    st.session_state.crash_start_time = None
    st.session_state.crash_cancelled = False

  # Geri Sayım Hesaplama
  crash_active_final = False
  if (
      st.session_state.crash_start_time is not None
      and not st.session_state.crash_cancelled
  ):
    elapsed = int(time.time() - st.session_state.crash_start_time)
    remaining = 15 - elapsed
    if remaining > 0:
      st.warning(
          f"🚨 **KAZA TİTREŞİMİ ALGILANDI!** İptal edilmezse tablet alarmı"
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

  # 1. Üst Başlık ve Kask Numarası
  st.markdown(
      f"""
        <div class="top-header">
            <div>
                <h2 style="margin:0; color:#fff; font-size:22px;">🪖 AKILLI KASK <span style="font-size:14px; background:#e94560; color:white; padding:2px 8px; border-radius:10px; margin-left:10px;">KASK-001</span></h2>
                <p style="margin:0; color:#8b949e; font-size:13px;">Güvenli Sürüş, Güvenli Yarınlar</p>
            </div>
            <div style="text-align:right;">
                <span style="color:#8b949e; font-size:13px;">📅 {now_str}</span><br>
                <span style="color:#3fb950; font-weight:bold; font-size:13px;">🟢 Bağlı • CANLI</span>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # 2. Sürücü Bilgisi
  st.markdown(
      """
        <div class="driver-box">
            👤 SÜRÜCÜ &nbsp;&nbsp;&nbsp;&nbsp; <b>Demo Sürücü</b>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # Alarm Durumu (SOS aktifse veya kaza 15 sn süresini doldurduysa tabletten ses çalar)
  alarm_durumu_aktif = (
      sos_val == 1 or crash_active_final or duman_val > 350
  ) and not st.session_state.manual_alarm_stop

  if alarm_durumu_aktif:
    st.markdown(
        """
            <div class="status-alert">
                🚨 TABLET SESLİ ALARMI ÇALIYOR! — SOS veya kaza teyit edildi!
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
                ✅ SİSTEM NORMAL — Aktif alarm yok
            </div>
        """,
        unsafe_allow_html=True,
    )

  # 4. 4'lü Metrik Kartları
  c1, c2, c3, c4 = st.columns(4)

  with c1:
    kaza_txt = "Kaza Var!" if is_crash_detected else "Kaza Yok (Normal)"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #f85149;">
                <div><b>🚨 KAZA DURUMU</b></div>
                <div style="font-size:16px; font-weight:bold; color:{'#f85149' if is_crash_detected else '#3fb950'};">{kaza_txt}</div>
                <div style="font-size:12px; color:#8b949e;">İvme: {round(ivme_val, 2)} g</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c2:
    gaz_txt = "Yüksek Gaz!" if duman_val > 350 else "Alkol / Kötü Gaz Yok"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #d29922;">
                <div><b>⚠️ ALKOL</b></div>
                <div style="font-size:16px; font-weight:bold; color:{'#d29922' if duman_val > 350 else '#3fb950'};">{gaz_txt}</div>
                <div style="font-size:12px; color:#8b949e;">Sensör Değeri: {duman_val}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c3:
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #58a6ff;">
                <div><b>📍 KONUM BİLGİSİ</b></div>
                <div style="font-size:15px; font-weight:bold; color:#58a6ff;">Tablet Konumu</div>
                <div style="font-size:11px; color:#8b949e;">Lat: {round(lat, 4)}, Lon: {round(lon, 4)}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c4:
    sos_txt = "AKTİF" if sos_val == 1 else "Pasif"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #ff7b72;">
                <div><b>🆘 SOS ÇAĞRISI</b></div>
                <div style="font-size:16px; font-weight:bold; color:{'#ff7b72' if sos_val == 1 else '#3fb950'};">{sos_txt}</div>
                <div style="font-size:12px; color:#8b949e;">Kask butonu ile kontrol edilir</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  st.write("")

  # Kontrol Butonları
  b_col1, b_col2 = st.columns(2)
  with b_col1:
    if st.button("🔴 ALARMI İPTAL ET", use_container_width=True):
      st.session_state.manual_alarm_stop = True
      st.session_state.crash_cancelled = True
      st.toast("Tablet alarmı susturuldu ve durum sıfırlandı!")
  with b_col2:
    if st.button("🔵 ALARMI AKTİFLEŞTİR", use_container_width=True):
      st.session_state.manual_alarm_stop = False
      st.toast("Alarm izleme modu yeniden açıldı.")

  st.markdown("---")

  # Harita ve Bilgi Bölümü (Merkezlenmiş İkon ve Uydu Görüntüsü)
  map_col, info_col = st.columns([2, 1])

  with map_col:
    st.markdown(
        "### 🛰️ GOOGLE EARTH UYDU GÖRÜNÜMÜ & MOTOSİKLET KASKI İŞARETÇİSİ"
    )

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
                    "anchorX": 64,  # İkonu yatayda tam ortalar
                    "anchorY": 64,  # İkonu dikeyde tam ortalar (kesilmeyi önler)
                }
            ],
        }
    )

    # 1. Ücretsiz Gerçek Uydu Katmanı (ESRI World Imagery)
    tile_layer = pdk.Layer(
        "TileLayer",
        data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        min_zoom=0,
        max_zoom=19,
        tileSize=256,
    )

    # 2. Parlayan Radar / Çember Efekti Katmanı
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        df_map,
        get_position="[lon, lat]",
        get_color=[0, 255, 200, 180],
        get_radius=70,
        radius_scale=6,
        radius_min_pixels=12,
        radius_max_pixels=40,
        get_line_color=[255, 255, 255, 200],
        get_line_width=3,
        pickable=True,
    )

    # 3. Motosiklet Kaskı Görsel İkon Katmanı (Tam Merkezli)
    icon_layer = pdk.Layer(
        "IconLayer",
        df_map,
        get_position="[lon, lat]",
        get_icon="icon_data",
        get_size=42,
        size_scale=1,
        pickable=True,
    )

    # 4. Kask ID Etiket Katmanı
    text_layer = pdk.Layer(
        "TextLayer",
        df_map,
        get_position="[lon, lat]",
        get_text="'🛡️ KASK-001 (Canlı)'",
        get_size=16,
        get_color=[255, 255, 255],
        get_background_color=[13, 17, 23, 230],
        get_alignment_baseline="'bottom'",
        get_pixel_offset=[0, -32],
    )

    view_state = pdk.ViewState(
        latitude=lat, longitude=lon, zoom=16, pitch=50, bearing=0
    )

    r = pdk.Deck(
        layers=[tile_layer, scatterplot_layer, icon_layer, text_layer],
        initial_view_state=view_state,
        map_style=None,
        tooltip={
            "text": (
                "Cihaz: KASK-001\nEnlem: {lat}\nBoylam:"
                " {lon}\nKoordinat Kaynağı: Canlı Tablet"
            )
        },
    )

    st.pydeck_chart(r, use_container_width=True)

  with info_col:
    st.markdown("### 📌 KONUM DETAYI")
    st.write(f"**Kaynak:** {konum_kaynagi}")
    st.caption(
        "Google Earth kalitesinde uydu katmanı ve tam merkezli kask simgesi"
        " aktif."
    )
    st.markdown("---")
    st.write(f"**Son Güncelleme:**\n{now_str}")
    st.write("**Cihaz ID:** KASK-001")
    st.write("**Sistem Durumu:** Çevrim İçi 🟢")


# Paneli Çalıştır
render_dashboard()
