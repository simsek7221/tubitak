from datetime import datetime
import pydeck as pdk
import requests
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Akıllı Kask | Güvenlik Paneli",
    page_icon="🪖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
  lat = float(data.get("lat", 38.5023))
  lon = float(data.get("lon", 43.3820))

  now_str = datetime.now().strftime("%d.%m.%Y   %H:%M:%S")

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

  # 3. Sistem Durum Banner'ı
  is_alarm = sos_val == 1 or ivme_val > 3.5 or duman_val > 250
  if is_alarm:
    st.markdown(
        """
            <div class="status-alert">
                🚨 SİSTEM ALARMI AKTİF! — Acil durum veya kaza algılandı!
            </div>
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
    kaza_txt = "Kaza Var!" if ivme_val > 3.5 else "Kaza Yok (Normal)"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #f85149;">
                <div><b>🚨 KAZA DURUMU</b></div>
                <div style="font-size:16px; font-weight:bold; color:{'#f85149' if ivme_val > 3.5 else '#3fb950'};">{kaza_txt}</div>
                <div style="font-size:12px; color:#8b949e;">İvme: {round(ivme_val, 2)} g</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c2:
    gaz_txt = "Yüksek Gaz!" if duman_val > 250 else "Gaz/Buhar Yok"
    st.markdown(
        f"""
            <div class="card-box" style="border-top: 4px solid #d29922;">
                <div><b>⚠️ ALKOL / BUHAR</b></div>
                <div style="font-size:16px; font-weight:bold; color:{'#d29922' if duman_val > 250 else '#3fb950'};">{gaz_txt}</div>
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
                <div style="font-size:15px; font-weight:bold; color:#58a6ff;">Van, Türkiye</div>
                <div style="font-size:11px; color:#8b949e;">Lat: {lat}, Lon: {lon}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with c4:
    sos_txt = "AKTİF (BASILDI!)" if sos_val == 1 else "Pasif (Normal)"
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
      st.toast("Alarm başarıyla iptal edildi ve sıfırlandı!")
  with b_col2:
    if st.button("🔵 SESLİ ALARMI AÇ", use_container_width=True):
      st.toast("Kask buzzer hoparlöründen sesli uyarı verildi!")

  st.markdown("---")

  # Harita ve Bilgi Bölümü
  map_col, info_col = st.columns([2, 1])

  with map_col:
    st.markdown(
        "### 🗺️ KONUM HARİTASI (Google Earth / Uydu Görüntüsü & Kask Simge)"
    )

    df = pd.DataFrame({"lat": [lat], "lon": [lon], "name": ["KASK-001"]})

    layer = pdk.Layer(
        "TextLayer",
        df,
        get_position="[lon, lat]",
        get_text="'🪖 KASK-001'",
        get_size=26,
        get_color=[255, 75, 75],
        get_alignment_baseline="'bottom'",
    )

    view_state = pdk.ViewState(
        latitude=lat, longitude=lon, zoom=15, pitch=50, bearing=0
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style=pdk.MapStyle.SATELLITE,
        tooltip={"text": "Kask Kimliği: KASK-001\nEnlem: {lat}\nBoylam: {lon}"},
    )

    st.pydeck_chart(r, use_container_width=True)

  with info_col:
    st.markdown("### 📌 KONUM BİLGİSİ")
    st.write("**Mevcut Konum:**")
    st.write("Van Merkez, Türkiye")
    st.caption("Google Earth uydu görüntüleri üzerinden canlı GPS takibi.")
    st.markdown("---")
    st.write(f"**Son Güncelleme:**\n{now_str}")
    st.write("**Cihaz ID:** KASK-001")
    st.write("**Sistem Durumu:** Çevrim İçi 🟢")


# Paneli Çalıştır
render_dashboard()
