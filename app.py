import time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# Sayfa ayarları
st.set_page_config(
    page_title="HIVE-MAP | Cyber Radar",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --- Tema / Stil (Cyberpunk Neon) ---
NEON_LIME = "#A6FF00"
ELECTRIC_BLUE = "#00D9FF"
DEEP_BG = "#05060A"
PANEL_BG = "#0B1020"
GRID = "#142033"
MUTED = "#A9B4C4"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800&display=swap');

html, body, [class*="css"] {{
  font-family: 'Orbitron', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
}}

.stApp {{
  background: radial-gradient(1200px 800px at 70% 20%, rgba(0,217,255,0.12), transparent 60%),
              radial-gradient(900px 700px at 20% 80%, rgba(166,255,0,0.10), transparent 55%),
              {DEEP_BG};
}}

div[data-testid="stMetric"] {{
  background: linear-gradient(180deg, rgba(11,16,32,0.96), rgba(11,16,32,0.72));
  border: 1px solid rgba(0,217,255,0.25);
  box-shadow: 0 0 24px rgba(0,217,255,0.18);
  border-radius: 14px;
  padding: 14px 14px 8px 14px;
}}
div[data-testid="stMetric"] * {{
  color: #EAF2FF !important;
}}

.cy-panel {{
  background: linear-gradient(180deg, rgba(11,16,32,0.96), rgba(11,16,32,0.70));
  border: 1px solid rgba(166,255,0,0.22);
  box-shadow: 0 0 26px rgba(166,255,0,0.16);
  border-radius: 18px;
  padding: 16px 18px 12px 18px;
}}

.cy-title {{
  text-align: center;
  margin-top: 6px;
  margin-bottom: 0px;
  font-weight: 800;
  letter-spacing: 1.8px;
  color: #EAF2FF;
}}
.cy-sub {{
  text-align: center;
  margin-top: 4px;
  margin-bottom: 10px;
  color: {MUTED};
}}
.cy-badge {{
  display: inline-block;
  padding: 6px 11px;
  border-radius: 999px;
  border: 1px solid rgba(0,217,255,0.3);
  background: rgba(0,217,255,0.10);
  color: {ELECTRIC_BLUE};
  font-size: 12px;
  letter-spacing: 0.8px;
}}

/* Canlı Veri Akışı göstergesi */
.live-pill {{
  position: fixed;
  top: 14px;
  right: 18px;
  z-index: 1000;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(15, 120, 40, 0.35);
  border: 1px solid rgba(166,255,0,0.9);
  color: {NEON_LIME};
  font-size: 11px;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  box-shadow: 0 0 18px rgba(166,255,0,0.5);
  display: flex;
  align-items: center;
  gap: 6px;
}}
.live-dot {{
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: {NEON_LIME};
  box-shadow: 0 0 16px rgba(166,255,0,0.9);
}}

section.main > div.block-container {{
  padding-top: 1.3rem;
  padding-bottom: 1.2rem;
}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='live-pill'><div class='live-dot'></div><span>Canlı Veri Akışı Aktif</span></div>",
    unsafe_allow_html=True,
)


# --- Yardımcı fonksiyonlar ---

def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def generate_radar_data(n_points: int, max_range: float):
    """Rastgele ama gerçekçi radar noktaları (RSSI ~ mesafe ilişkili)."""
    theta = np.linspace(0, 360, n_points, endpoint=False)
    base_r = np.random.uniform(1.0, max_range, size=n_points)
    base_r.sort()
    base_r = base_r[::-1]  # En güçlü sinyaller merkeze yakın
    r = np.clip(base_r, 1.0, max_range)

    # RSSI: -35 dBm (çok güçlü) ile -90 dBm (zayıf) arası
    r_norm = (r - 1.0) / (max_range - 1.0 + 1e-6)
    rssi = -35 - r_norm * 50 + np.random.normal(0, 2.0, size=n_points)

    return r, theta, rssi


def build_radar_figure(max_range: float):
    n_points = np.random.randint(5, 13)
    r, theta, rssi = generate_radar_data(n_points, max_range)

    sizes = 12 + (np.max(rssi) - rssi)  # daha güçlü sinyal → daha büyük
    sizes = np.clip(sizes, 10, 26)

    labels = [f"NODE-{i+1:02d}" for i in range(n_points)]
    hover = [
        f"{lbl}<br>RSSI: {val:.0f} dBm<br>Range: {rr:.1f} m"
        for lbl, val, rr in zip(labels, rssi, r)
    ]

    fig = go.Figure()

    # Grid halkaları
    for rr in np.linspace(max_range / 4, max_range, 4):
        fig.add_trace(
            go.Scatterpolar(
                r=[rr] * 361,
                theta=list(range(361)),
                mode="lines",
                line=dict(color="rgba(0,255,120,0.25)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # Sweep çizgisi (tek frame için bile animasyon hissi)
    sweep_angle = np.random.uniform(0, 360)
    fig.add_trace(
        go.Scatterpolar(
            r=[0, max_range],
            theta=[sweep_angle, sweep_angle],
            mode="lines",
            line=dict(color="rgba(166,255,0,0.85)", width=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Hedefler
    fig.add_trace(
        go.Scatterpolar(
            r=r,
            theta=theta,
            mode="markers",
            marker=dict(
                size=sizes,
                color=NEON_LIME,
                symbol="cross",
                line=dict(color="rgba(0,0,0,0.85)", width=1.4),
            ),
            text=hover,
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG,
        margin=dict(l=16, r=16, t=18, b=10),
        font=dict(color=NEON_LIME),
        polar=dict(
            bgcolor="#020806",
            radialaxis=dict(
                range=[0, max_range],
                showticklabels=False,
                ticks="",
                gridcolor="rgba(0,255,100,0.35)",
            ),
            angularaxis=dict(
                showticklabels=False,
                ticks="",
                gridcolor="rgba(0,255,100,0.15)",
            ),
        ),
    )
    return fig


def generate_fft_data(n_bins: int = 170):
    """Rastgele ama insan sesi / ortam gürültüsüne benzeyen FFT eğrisi."""
    freqs = np.linspace(0, 4000, n_bins)

    peaks = [
        (np.random.uniform(120, 220), 0.9),
        (np.random.uniform(350, 600), 0.7),
        (np.random.uniform(1000, 1500), 0.5),
        (np.random.uniform(2200, 2800), 0.35),
    ]
    amp = np.zeros_like(freqs)
    for center, gain in peaks:
        width = np.random.uniform(70, 140)
        amp += gain * np.exp(-0.5 * ((freqs - center) / width) ** 2)

    # Yüksek frekanslarda biraz gürültü
    amp += 0.06 * np.random.rand(n_bins)
    amp = np.clip(amp, 0, 1.0)
    return freqs, amp


def build_fft_figure():
    freqs, amp = generate_fft_data()
    df = pd.DataFrame({"Hz": freqs, "Amp": amp})

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Hz"],
            y=df["Amp"],
            mode="lines",
            line=dict(color=ELECTRIC_BLUE, width=2.6),
            hovertemplate="Hz: %{x:.0f}<br>Amp: %{y:.2f}<extra></extra>",
            name="Spectrum",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Hz"],
            y=df["Amp"].rolling(6, min_periods=1).mean(),
            mode="lines",
            line=dict(color=NEON_LIME, width=1.4),
            opacity=0.9,
            hoverinfo="skip",
            name="Smoothed",
        )
    )

    fig.update_layout(
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG,
        margin=dict(l=16, r=16, t=18, b=10),
        font=dict(color="#EAF2FF"),
        xaxis=dict(
            title="Frequency (Hz)",
            gridcolor=GRID,
            zeroline=False,
            linecolor="rgba(255,255,255,0.12)",
        ),
        yaxis=dict(
            title="Amplitude",
            gridcolor=GRID,
            zeroline=False,
            range=[0, 1.05],
            linecolor="rgba(255,255,255,0.12)",
        ),
        showlegend=False,
    )
    peak_level = float(np.max(amp))
    return fig, peak_level


# --- Başlık ---
st.markdown(
    "<div class='cy-title' style='font-size:34px'>HIVE-MAP // CYBER RADAR CONSOLE</div>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<div class='cy-sub'>Sanal Sürü Sensör Ağı • "
    f"<span class='cy-badge'>DARK • NEON • SIMULATED</span></div>",
    unsafe_allow_html=True,
)
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# --- Üst Panel: Radar + FFT ---
col_radar, col_fft = st.columns(2, gap="large")

with col_radar:
    st.markdown("<div class='cy-panel'>", unsafe_allow_html=True)
    st.subheader("📡 Taktik Neon Radar")
    radar_range = 15.0
    radar_fig = build_radar_figure(radar_range)
    st.plotly_chart(
        radar_fig,
        use_container_width=True,
        config={"displayModeBar": False},
        key="radar_graph_main",  # benzersiz key
    )
    st.caption("Rastgele üretilen düğümler • RSSI → menzil/yoğunluk (tamamen simülasyon)")
    st.markdown("</div>", unsafe_allow_html=True)

with col_fft:
    st.markdown("<div class='cy-panel'>", unsafe_allow_html=True)
    st.subheader("🎙️ Akustik Spektrum Analizi (Simüle FFT)")
    fft_fig, fft_peak = build_fft_figure()
    st.plotly_chart(
        fft_fig,
        use_container_width=True,
        config={"displayModeBar": False},
        key="fft_graph_main",  # benzersiz key
    )
    if fft_peak > 0.65:
        st.markdown(
            "<div style='padding:6px 10px;margin-bottom:4px;border-radius:10px;"
            "background:rgba(255,0,80,0.20);border:1px solid rgba(255,0,80,0.80);"
            "color:#FFECEC;font-weight:800;text-align:center;letter-spacing:1.1px;'>"
            "SES TEPESİ SİMÜLE EDİLDİ</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='padding:4px 8px;margin-bottom:4px;border-radius:8px;"
            "background:rgba(0,200,120,0.15);border:1px solid rgba(0,200,120,0.65);"
            "color:#D8FFE0;font-size:11px;text-align:center;'>"
            "Arka plan gürültüsü seviyesi normal (simülasyon)</div>",
            unsafe_allow_html=True,
        )
    st.caption("Tüm veriler numpy ile rastgele üretilir; gerçek mikrofon kullanılmaz.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


# --- Alt Panel: Telemetri ---
st.markdown("<div class='cy-panel'>", unsafe_allow_html=True)
st.subheader("📊 Sistem Telemetri Özeti")

m1, m2, m3, m4 = st.columns(4, gap="large")

# Cihaz sayısı: 3–8 arası
device_count = int(np.random.randint(3, 9))

# Batarya: %35–%98 arası, hafif dalgalı
battery = int(np.clip(np.random.normal(78, 8), 35, 98))

# Bağlantı kalitesi: %70–%100 arası
link_quality = int(np.clip(np.random.normal(93, 4), 70, 100))

# Gürültü bastırma durumu (deep learning filtresi)
noise_eff = int(np.clip(np.random.normal(84, 6), 40, 99))

m1.metric("Tespit Edilen Cihaz", device_count, delta="Canlı tarama (simülasyon)")
m2.metric("Bağlantı Kalitesi", f"%{link_quality}", delta="Şifreli mesh uplink")
m3.metric("Batarya", f"%{battery}", delta="Taktik güç yönetimi")
m4.metric("Gürültü Bastırma", "Aktif - DeepLearning Filtresi", delta=f"%{noise_eff}")

st.caption(
    f"Son güncelleme: {ts()} • Tüm değerler demo amacıyla istatistiksel olarak üretilmiştir."
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)


# --- Alt kısım: Büyük SİSTEMİ GÜNCELLE / TARA butonu ---
st.markdown(
    "<div style='text-align:center;'>",
    unsafe_allow_html=True,
)
update_clicked = st.button(
    "🔁 SİSTEMİ GÜNCELLE / TARA",
    use_container_width=True,
)
st.markdown("</div>", unsafe_allow_html=True)

if update_clicked:
    # Tüm verileri yeniden üretmek için sayfayı baştan yükle
    st.rerun()
