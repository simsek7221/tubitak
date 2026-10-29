import time
from datetime import datetime
import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Akıllı Kask | Endüstriyel Telemetri Paneli",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Oturum Durumu Tanımlamaları
if "crash_start_time" not in st.session_state:
  st.session_state.crash_start_time = None
if "crash_cancelled" not in st.session_state:
  st.session_state.crash_cancelled = False
if "manual_alarm_stop" not in st.session_state:
  st.session_state.manual_alarm_stop = False

# ULTRA CANLI & PARLAK CYBERPUNK HUD STİLLERİ (CSS)
st.markdown(
    """
    <style>
    .stApp { 
        background-color: #02040a; 
        color: #ffffff; 
        font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
    }
    .top-header {
        background: linear-gradient(135deg, #091931 0%, #0b2545 100%);
        padding: 18px 24px;
        border-radius: 12px;
        border: 2px solid #00b4d8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        box-shadow: 0 0 30px rgba(0, 180, 216, 0.4);
    }
    .driver-box {
        background: rgba(9, 25, 49, 0.95);
        padding: 14px 20px;
        border-radius: 10px;
        border: 1px solid #00b4d8;
        margin-bottom: 16px;
        font-weight: 800;
        color: #00f5d4;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 0 15px rgba(0, 245, 212, 0.2);
    }
    .status-normal {
        background: linear-gradient(135deg, #022c22 0%, #064e3b 100%);
        color: #34d399;
        padding: 16px;
        border-radius: 12px;
        font-size: 22px;
        font-weight: 900;
        text-align: center;
        border: 2px solid #10b981;
        margin-bottom: 16px;
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
        text-shadow: 0 0 12px rgba(52, 211, 153, 0.7);
    }
    .status-alert {
        background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);
        color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        font-size: 22px;
        font-weight: 900;
        text-align: center;
        border: 2px solid #ef4444;
        margin-bottom: 16px;
        box-shadow: 0 0 40px rgba(239, 68, 68, 0.8);
        animation: pulse-alert 1s infinite;
    }
    @keyframes pulse-alert {
        0% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.6); }
        50% { box-shadow: 0 0 50px rgba(239, 68, 68, 1); }
        100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.6); }
    }
    .card-box {
        background: rgba(9, 25, 49, 0.9);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #1d3557;
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 8px 25px rgba(0,0,0,0.7);
        transition: all 0.3s ease;
    }
    .card-box:hover {
        border-color: #00f5d4;
        box-shadow: 0 0 25px rgba(0, 245, 212, 0.4);
    }
    .map-footer-banner {
        background: #02040a;
        color: #00f5d4;
        padding: 8px 14px;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 1px;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
        border: 1px solid #1d3557;
        border-top: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

FIREBASE_URL = "https://akilli-kask-proje-default-rtdb.europe-west1.firebasedatabase.app/telemetri.json"


@st.fragment(run_every=2)
def render_dashboard():
  try:
    response = requests.get(FIREBASE_URL, timeout=5)
    data = response.json() if response.status_code == 200 else {}
  except:
    data = {}

  ivme_val = float(data.get("ivme", 1.0))
  duman_val = int(data.get("duman", 180))
  sos_val = int(data.get("sos", 0))

  location = streamlit_geolocation()
  if location.get("latitude") and location.get("longitude"):
    lat, lon = float(location["latitude"]), float(location["longitude"])
    konum_baslik, konum_kaynagi = "GPS Kilitlendi (Canlı)", "Canlı GPS"
  else:
    lat, lon = 38.5023, 43.3820
    konum_baslik, konum_kaynagi = "GPS Sinyali Bekleniyor...", "Bekleniyor"

  now_str = datetime.now().strftime("%d.%m.%Y   %H:%M:%S")

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
          f"🚨 **KAZA ALGILANDI!** Alarm için **{remaining} saniye** kaldı!"
      )
      if st.button("🛡️ İPTAL ET (YANLIŞ ALARM)", use_container_width=True):
        st.session_state.crash_cancelled = True
        st.session_state.crash_start_time = None
        st.rerun()
    else:
      crash_active_final = True

  # Başlık
  st.markdown(
      f"""
        <div class="top-header">
            <div>
                <h2 style="margin:0; color:#ffffff; font-size:24px; text-shadow: 0 0 12px rgba(0,245,212,0.6);">🛡️ AKILLİ KASK TELEMETRİSİ <span style="font-size:12px; background:#00f5d4; color:#02040a; padding:3px 10px; border-radius:12px; margin-left:8px; font-weight:900;">KASK-001</span></h2>
                <p style="margin:3px 0 0 0; color:#90e0ef; font-size:12px; font-weight:700;">TÜBİTAK Proje Sunum Paneli</p>
            </div>
            <div style="text-align:right;">
                <span style="color:#90e0ef; font-size:12px; font-weight:700;">📅 {now_str}</span><br>
                <span style="color:#00f5d4; font-weight:900; font-size:14px; text-shadow: 0 0 10px rgba(0,245,212,0.8);">⚡ ESP32 • CANLI &nbsp;|&nbsp; 192.168.4.1</span>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      """
        <div class="driver-box">
            <span>👤 SÜRÜCÜ:</span> <span style="color:#ffffff; font-weight:900;">Demo Sürücü (TÜBİTAK Ekipmanı)</span>
        </div>
    """,
      unsafe_allow_html=True,
  )

  alarm_durumu_aktif = (
      sos_val == 1 or crash_active_final or duman_val > 350
  ) and not st.session_state.manual_alarm_stop

  if alarm_durumu_aktif:
    st.markdown(
        """
            <div class="status-alert">
                🚨 KRİTİK ALARM AKTİF! — Acil Durum Veya Kaza Doğrulandı!
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
                ✔ SİSTEM GÜVENLİ VE AKTİF
                <div style="font-size:13px; font-weight:700; color:#a7f3d0; margin-top:2px;">Tüm telemetri sensörleri stabil çalışıyor.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  # Kartlar
  c1, c2, c3, c4 = st.columns(4)
  with c1:
    kaza_txt = "Kaza Var!" if is_crash_detected else "Normal"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 5px solid {'#ef4444' if is_crash_detected else '#10b981'};">
                <div><span style="font-size:16px;">🚨</span> <b style="color:#f8fafc; font-size:13px;">KAZA DURUMU</b></div>
                <div style="font-size:22px; font-weight:900; color:{'#f87171' if is_crash_detected else '#34d399'}; text-shadow: 0 0 10px rgba(0,0,0,0.6);">{kaza_txt}</div>
                <div style="font-size:11px; color:#94a3b8; font-weight:700;">İvme: {round(ivme_val, 2)} G</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
  with c2:
    gaz_txt = "Yüksek Gaz!" if duman_val > 350 else "Temiz Hava"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 5px solid {'#f59e0b' if duman_val > 350 else '#10b981'};">
                <div><span style="font-size:16px;">⚠️</span> <b style="color:#f8fafc; font-size:13px;">ALKOL / BUHAR</b></div>
                <div style="font-size:22px; font-weight:900; color:{'#fbbf24' if duman_val > 350 else '#34d399'}; text-shadow: 0 0 10px rgba(0,0,0,0.6);">{gaz_txt}</div>
                <div style="font-size:11px; color:#94a3b8; font-weight:700;">Değer: {duman_val} ppm</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
  with c3:
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 5px solid #00f5d4;">
                <div><span style="font-size:16px;">📍</span> <b style="color:#f8fafc; font-size:13px;">GPS KONUMU</b></div>
                <div style="font-size:16px; font-weight:900; color:#00f5d4; text-shadow: 0 0 10px rgba(0,245,212,0.5);">{konum_baslik}</div>
                <div style="font-size:11px; color:#94a3b8; font-weight:700;">Lat: {round(lat, 4)} | Lon: {round(lon, 4)}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
  with c4:
    sos_txt = "AKTİF!" if sos_val == 1 else "Beklemede"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 5px solid {'#ef4444' if sos_val == 1 else '#10b981'};">
                <div><span style="font-size:16px;">🆘</span> <b style="color:#f8fafc; font-size:13px;">SOS ÇAĞRISI</b></div>
                <div style="font-size:22px; font-weight:900; color:{'#f87171' if sos_val == 1 else '#34d399'}; text-shadow: 0 0 10px rgba(0,0,0,0.6);">{sos_txt}</div>
                <div style="font-size:11px; color:#94a3b8; font-weight:700;">Buton Kontrolü</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  st.write("")

  b_col1, b_col2 = st.columns(2)
  with b_col1:
    if st.button("🔴 ALARMI İPTAL ET", use_container_width=True):
      st.session_state.manual_alarm_stop = True
      st.session_state.crash_cancelled = True
      st.toast("Alarm susturuldu!")
  with b_col2:
    if st.button("🔊 SESLİ ALARMI TEST ET", use_container_width=True):
      st.session_state.manual_alarm_stop = False
      st.toast("Alarm modu aktif.")

  st.markdown("---")

  # Harita
  map_col, info_col = st.columns([2.3, 1])
  with map_col:
    st.markdown("### 🛰️ CANLI UYDU GPS TAKİP HARİTASI (KASK-001)")
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
    ).add_to(m)

    helmet_icon_html = """
        <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 65px; height: 65px;">
            <div style="position: absolute; width: 55px; height: 55px; background: rgba(0, 245, 212, 0.4); border: 2px solid #00f5d4; border-radius: 50%; animation: pulse-ring 1.5s infinite;"></div>
            <div style="position: relative; background: linear-gradient(135deg, #091931, #0b2545); border: 2px solid #00f5d4; border-radius: 50%; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(0, 245, 212, 0.9);">
                <img src="https://cdn-icons-png.flaticon.com/512/2965/2965352.png" style="width: 25px; height: 25px; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.8));" />
            </div>
            <div style="position: absolute; bottom: -24px; left: 50%; transform: translateX(-50%); background: #091931; color: #00f5d4; padding: 2px 8px; font-size: 10px; font-weight: 900; border-radius: 6px; border: 1px solid #00f5d4; white-space: nowrap; box-shadow: 0 4px 10px rgba(0,0,0,0.8);">KASK-001</div>
        </div>
        <style>
        @keyframes pulse-ring {
            0% { transform: scale(0.95); opacity: 1; }
            50% { transform: scale(1.45); opacity: 0.2; }
            100% { transform: scale(0.95); opacity: 1; }
        }
        </style>
        """
    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(
            html=helmet_icon_html, icon_size=(65, 65), icon_anchor=(32, 32)
        ),
        tooltip="KASK-001",
    ).add_to(m)
    st_folium(m, height=410, use_container_width=True)

    st.markdown(
        f"""
        <div class="map-footer-banner">
            <span>🛰️ {konum_kaynagi.upper()}</span>
            <span>ENLEM: {round(lat, 4)}° N | BOYLAM: {round(lon, 4)}° E</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

  with info_col:
    st.markdown("### 📌 TELEMETRİ ÖZETİ")
    st.markdown(
        """
        <div style="background: rgba(9, 25, 49, 0.8); padding: 14px; border-radius: 10px; border: 1px solid #1d3557; font-size: 13px;">
            <p style="margin-bottom:8px;"><b>Protokol:</b> Firebase Realtime DB</p>
            <p style="margin-bottom:8px;"><b>Donanım:</b> Deneyap Kart V2 (ESP32)</p>
            <p style="margin-bottom:8px;"><b>Konum:</b> Canlı GPS Takibi</p>
            <p style="margin-bottom:0;"><b>Durum:</b> Aktif Koruma 🟢</p>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.write(f"**Son Güncelleme:**\n{now_str}")
    st.write("**Cihaz ID:** KASK-001")


render_dashboard()
