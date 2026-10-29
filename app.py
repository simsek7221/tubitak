import time
from datetime import datetime
import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

# ==========================================
# 1. SAYFA YAPILANDIRMASI VE GENEL AYARLAR
# ==========================================
st.set_page_config(
    page_title="Akıllı Kask | Endüstriyel Telemetri Paneli",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Oturum Durumu (Session State) Tanımlamaları
if "crash_start_time" not in st.session_state:
  st.session_state.crash_start_time = None
if "crash_cancelled" not in st.session_state:
  st.session_state.crash_cancelled = False
if "manual_alarm_stop" not in st.session_state:
  st.session_state.manual_alarm_stop = False

# ==========================================
# 2. ULTRA MODERN KASK HUD TASARIM STİLLERİ (CSS)
# ==========================================
st.markdown(
    """
    <style>
    /* Genel Arka Plan ve Tipografi */
    .stApp { 
        background-color: #030712; 
        color: #f3f4f6; 
        font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
    }
    
    /* Üst Başlık Konsolu */
    .top-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        padding: 16px 24px;
        border-radius: 12px;
        border: 1px solid #312e81;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.7);
    }
    
    /* Sürücü Bilgi Paneli */
    .driver-box {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        padding: 12px 20px;
        border-radius: 10px;
        border: 1px solid #1e293b;
        margin-bottom: 16px;
        font-weight: 600;
        color: #38bdf8;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* Sistem Normal Durumu (Neon Yeşil) */
    .status-normal {
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.8), rgba(4, 47, 46, 0.9));
        backdrop-filter: blur(12px);
        color: #34d399;
        padding: 16px;
        border-radius: 12px;
        font-size: 20px;
        font-weight: 700;
        text-align: center;
        border: 1px solid #059669;
        margin-bottom: 16px;
        box-shadow: 0 0 20px rgba(52, 211, 153, 0.15);
    }
    
    /* Kritik Alarm Durumu (Parlayan Kırmızı HUD) */
    .status-alert {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.9), rgba(153, 27, 27, 0.9));
        backdrop-filter: blur(12px);
        color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        font-size: 20px;
        font-weight: 700;
        text-align: center;
        border: 1px solid #dc2626;
        margin-bottom: 16px;
        box-shadow: 0 0 30px rgba(220, 38, 38, 0.5);
        animation: pulse-alert 1.5s infinite;
    }
    
    @keyframes pulse-alert {
        0% { box-shadow: 0 0 15px rgba(220, 38, 38, 0.4); }
        50% { box-shadow: 0 0 35px rgba(220, 38, 38, 0.8); }
        100% { box-shadow: 0 0 15px rgba(220, 38, 38, 0.4); }
    }

    /* Metrik Kartları (Glassmorphism) */
    .card-box {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(10px);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #1e293b;
        height: 155px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        transition: transform 0.2s ease;
    }
    .card-box:hover {
        border-color: #475569;
    }
    
    /* Harita Alt Bilgi Bandı */
    .map-footer-banner {
        background: rgba(3, 7, 18, 0.9);
        color: #94a3b8;
        padding: 8px 14px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
        border: 1px solid #1e293b;
        border-top: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Firebase Veritabanı Uç Noktası
FIREBASE_URL = "https://akilli-kask-proje-default-rtdb.europe-west1.firebasedatabase.app/telemetri.json"


# ==========================================
# 3. CANLI AKIŞ VE KONTROL FONKSİYONU (2 Sn)
# ==========================================
@st.fragment(run_every=2)
def render_dashboard():
  try:
    response = requests.get(FIREBASE_URL, timeout=5)
    if response.status_code == 200:
      data = response.json() or {}
    else:
      data = {}
  except:
    data = {}

  # Sensör Değerleri
  ivme_val = float(data.get("ivme", 1.0))
  duman_val = int(data.get("duman", 180))
  sos_val = int(data.get("sos", 0))

  # Otomatik ve Kesintisiz GPS Konum Tespiti
  location = streamlit_geolocation()
  if location.get("latitude") and location.get("longitude"):
    lat = float(location["latitude"])
    lon = float(location["longitude"])
    konum_baslik = "GPS Kilitlendi (Canlı)"
    konum_alt_metin = "Anlık Uydu Takibi Aktif"
    konum_kaynagi = "Canlı GPS Koordinatı"
  else:
    lat, lon = 38.5023, 43.3820  # Sinyal beklenirken referans koordinat
    konum_baslik = "GPS Aranıyor..."
    konum_alt_metin = "Uydu bağlantısı bekleniyor"
    konum_kaynagi = "GPS Sinyali Bekleniyor"

  now_str = datetime.now().strftime("%d.%m.%Y   %H:%M:%S")

  # Kaza Algılama ve 15 Saniye Geri Sayım Emniyet Mekanizması
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
          f" tetiklenecek: **{remaining} saniye** kaldı!"
      )
      if st.button(
          "🛡️ KAZAYI İPTAL ET (YANLIŞ ALARM)", use_container_width=True
      ):
        st.session_state.crash_cancelled = True
        st.session_state.crash_start_time = None
        st.rerun()
    else:
      crash_active_final = True

  # ------------------------------------------
  # ARAYÜZ BİLEŞENLERİNİN OLUŞTURULMASI
  # ------------------------------------------

  # Üst Başlık Konsolu
  st.markdown(
      f"""
        <div class="top-header">
            <div>
                <h2 style="margin:0; color:#ffffff; font-size:22px; letter-spacing:0.5px;">🛡️ AKILLI KASK TELEMETRİSİ <span style="font-size:12px; background:#0284c7; color:white; padding:3px 10px; border-radius:12px; margin-left:8px; font-weight:600;">KASK-001</span></h2>
                <p style="margin:3px 0 0 0; color:#94a3b8; font-size:12px;">TÜBİTAK Proje Sunum ve Canlı Takip Paneli</p>
            </div>
            <div style="text-align:right;">
                <span style="color:#94a3b8; font-size:12px;">📅 {now_str}</span><br>
                <span style="color:#34d399; font-weight:700; font-size:12px;">⚡ ESP32 • CANLI &nbsp;|&nbsp; 192.168.4.1</span>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # Sürücü Bilgisi
  st.markdown(
      """
        <div class="driver-box">
            <span>👤 SÜRÜCÜ PROFİLİ:</span> <span style="color:#ffffff; font-weight:700;">Demo Sürücü (TÜBİTAK Test Ekipmanı)</span>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # Sistem Durum Paneli & Sesli Alarm Tetikleyicisi
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
                <div style="font-size:12px; font-weight:normal; color:#94a3b8; margin-top:2px;">Tüm telemetri sensörleri normal değerlerde çalışıyor.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  # 4'lü Endüstriyel Metrik Kartları
  c1, c2, c3, c4 = st.columns(4)

  with c1:
    kaza_txt = "Kaza Var!" if is_crash_detected else "Normal"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid {'#ef4444' if is_crash_detected else '#10b981'};">
                <div><span style="font-size:16px;">🚨</span> <b style="color:#e2e8f0; font-size:13px;">KAZA DURUMU</b></div>
                <div style="font-size:18px; font-weight:800; color:{'#ef4444' if is_crash_detected else '#34d399'};">{kaza_txt}</div>
                <div style="font-size:11px; color:#94a3b8;">İvme Sensörü: {round(ivme_val, 2)} G</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c2:
    gaz_txt = "Yüksek Gaz!" if duman_val > 350 else "Temiz Hava"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid {'#f59e0b' if duman_val > 350 else '#10b981'};">
                <div><span style="font-size:16px;">⚠️</span> <b style="color:#e2e8f0; font-size:13px;">ALKOL / BUHAR</b></div>
                <div style="font-size:18px; font-weight:800; color:{'#f59e0b' if duman_val > 350 else '#34d399'};">{gaz_txt}</div>
                <div style="font-size:10px; color:#94a3b8; line-height:1.2;">Sensör Ölçümü: {duman_val} ppm</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c3:
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #38bdf8;">
                <div><span style="font-size:16px;">📍</span> <b style="color:#e2e8f0; font-size:13px;">GPS KONUMU</b></div>
                <div style="font-size:15px; font-weight:800; color:#ffffff;">{konum_baslik}</div>
                <div style="font-size:10px; color:#94a3b8; line-height:1.2;">Lat: {round(lat, 4)} | Lon: {round(lon, 4)}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c4:
    sos_txt = "AKTİF!" if sos_val == 1 else "Beklemede"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid {'#ef4444' if sos_val == 1 else '#10b981'};">
                <div><span style="font-size:16px;">🆘</span> <b style="color:#e2e8f0; font-size:13px;">SOS ÇAĞRISI</b></div>
                <div style="font-size:18px; font-weight:800; color:{'#ef4444' if sos_val == 1 else '#34d399'};">{sos_txt}</div>
                <div style="font-size:11px; color:#94a3b8;">Donanımsal Buton</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  st.write("")

  # Kontrol Butonları
  b_col1, b_col2 = st.columns(2)
  with b_col1:
    if st.button("🔴 ACİL ALARMI İPTAL ET", use_container_width=True):
      st.session_state.manual_alarm_stop = True
      st.session_state.crash_cancelled = True
      st.toast("Alarm başarıyla susturuldu ve sıfırlandı!")
  with b_col2:
    if st.button("🔊 SESLİ ALARMI TEST ET", use_container_width=True):
      st.session_state.manual_alarm_stop = False
      st.toast("Alarm izleme modu aktifleştirildi.")

  st.markdown("---")

  # ------------------------------------------
  # 4. HARİTA VE UYDU GÖRÜNÜMÜ BÖLÜMÜ
  # ------------------------------------------
  map_col, info_col = st.columns([2.3, 1])

  with map_col:
    st.markdown("### 🛰️ CANLI UYDU GPS TAKİP HARİTASI (KASK-001)")

    # Folium Haritası Oluşturma
    m = folium.Map(
        location=[lat, lon],
        zoom_start=16,
        tiles=None,
        control_scale=True,
    )

    # Esri World Imagery (Renkli Yüksek Çözünürlüklü Uydu Katmanı)
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri World Imagery",
        name="Uydu Görüntüsü",
    ).add_to(m)

    # Modern Motosiklet Kaskı ve Neon Halka İçeren Özel HTML Markeri
    helmet_icon_html = """
    <div style="
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 60px;
        height: 60px;
    ">
        <div style="
            position: absolute;
            width: 50px;
            height: 50px;
            background: rgba(56, 189, 248, 0.25);
            border: 2px solid #38bdf8;
            border-radius: 50%;
            animation: pulse-ring 2s infinite;
        "></div>
        <div style="
            position: relative;
            background: linear-gradient(135deg, #0f172a, #1e1b4b);
            border: 2px solid #38bdf8;
            border-radius: 50%;
            width: 42px;
            height: 42px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.7);
        ">
            <img src="https://cdn-icons-png.flaticon.com/512/2965/2965352.png" style="width: 24px; height: 24px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.6));" />
        </div>
        <div style="
            position: absolute;
            bottom: -22px;
            left: 50%;
            transform: translateX(-50%);
            background: #0f172a;
            color: #38bdf8;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 800;
            border-radius: 6px;
            border: 1px solid #38bdf8;
            white-space: nowrap;
            box-shadow: 0 4px 6px rgba(0,0,0,0.5);
            letter-spacing: 0.5px;
        ">KASK-001</div>
    </div>
    
    <style>
    @keyframes pulse-ring {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.35); opacity: 0.2; }
        100% { transform: scale(0.95); opacity: 0.8; }
    }
    </style>
    """

    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(
            html=helmet_icon_html, icon_size=(60, 60), icon_anchor=(30, 30)
        ),
        tooltip="KASK-001 (Canlı GPS)",
    ).add_to(m)

    # Haritayı Render Et
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
        <div style="background: rgba(15, 23, 42, 0.6); padding: 14px; border-radius: 10px; border: 1px solid #1e293b; font-size: 13px;">
            <p style="margin-bottom:8px;"><b>Bağlantı Protokolü:</b> Firebase Realtime DB</p>
            <p style="margin-bottom:8px;"><b>Donanım Birimi:</b> Deneyap Kart V2 (ESP32)</p>
            <p style="margin-bottom:8px;"><b>Konum Servisi:</b> Otomatik Canlı GPS</p>
            <p style="margin-bottom:0;"><b>Güvenlik Modu:</b> Aktif Koruma 🟢</p>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.write(f"**Son Güncelleme:**\n{now_str}")
    st.write("**Cihaz ID:** KASK-001")
    st.write("**Sistem Durumu:** Çevrim İçi 🟢")


# Paneli Çalıştır
render_dashboard()
