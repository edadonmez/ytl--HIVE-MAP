import time
from datetime import datetime
from collections import deque

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    import sounddevice as sd

    HAS_SOUND = True
except Exception:
    HAS_SOUND = False

try:
    from pywifi import PyWiFi, const

    HAS_WIFI = True
except Exception:
    HAS_WIFI = False


st.set_page_config(
    page_title="HIVE-MAP | Cyber Command",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
  background: radial-gradient(1200px 800px at 70% 20%, rgba(0,217,255,0.10), transparent 60%),
              radial-gradient(900px 700px at 20% 80%, rgba(166,255,0,0.08), transparent 55%),
              {DEEP_BG};
}}

div[data-testid="stMetric"] {{
  background: linear-gradient(180deg, rgba(11,16,32,0.95), rgba(11,16,32,0.70));
  border: 1px solid rgba(0,217,255,0.18);
  box-shadow: 0 0 22px rgba(0,217,255,0.10);
  border-radius: 14px;
  padding: 14px 14px 8px 14px;
}}
div[data-testid="stMetric"] * {{
  color: #EAF2FF !important;
}}

.cy-panel {{
  background: linear-gradient(180deg, rgba(11,16,32,0.92), rgba(11,16,32,0.62));
  border: 1px solid rgba(166,255,0,0.16);
  box-shadow: 0 0 26px rgba(166,255,0,0.10);
  border-radius: 16px;
  padding: 14px 16px 10px 16px;
}}

.cy-title {{
  text-align: center;
  margin-top: 6px;
  margin-bottom: 0px;
  font-weight: 800;
  letter-spacing: 1.6px;
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
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(0,217,255,0.22);
  background: rgba(0,217,255,0.06);
  color: {ELECTRIC_BLUE};
  font-size: 12px;
  letter-spacing: 0.8px;
}}
.logbox {{
  border: 1px solid rgba(0,217,255,0.18);
  background: rgba(5,6,10,0.55);
  border-radius: 12px;
  padding: 10px 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  color: #D8E6FF;
  max-height: 220px;
  overflow: auto;
}}
.logline {{
  white-space: pre-wrap;
  line-height: 1.35;
  font-size: 12px;
}}
.lvl-info {{ color: #D8E6FF; }}
.lvl-ok   {{ color: {NEON_LIME}; }}
.lvl-warn {{ color: #FFD166; }}
.lvl-err  {{ color: #FF4D6D; }}

/* Reduce Streamlit header padding */
section.main > div.block-container {{
  padding-top: 1.3rem;
  padding-bottom: 1.2rem;
}}
</style>
""",
    unsafe_allow_html=True,
)


def _ensure_state():
    if "radar_points" not in st.session_state:
        st.session_state.radar_points = []
    if "logs" not in st.session_state:
        st.session_state.logs = {
            "radar": deque(maxlen=14),
            "audio": deque(maxlen=14),
            "telemetry": deque(maxlen=10),
        }
    if "tick" not in st.session_state:
        st.session_state.tick = 0
    if "wifi_networks" not in st.session_state:
        st.session_state.wifi_networks = []
    if "last_wifi_scan_tick" not in st.session_state:
        st.session_state.last_wifi_scan_tick = -1000
    if "last_audio_alert_tick" not in st.session_state:
        st.session_state.last_audio_alert_tick = -1000


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def _push_log(channel: str, level: str, message: str):
    st.session_state.logs[channel].appendleft((level, f"[{_ts()}] {message}"))


def _render_logs(channel: str):
    lines = []
    for lvl, msg in st.session_state.logs[channel]:
        cls = {
            "INFO": "lvl-info",
            "OK": "lvl-ok",
            "WARN": "lvl-warn",
            "ERR": "lvl-err",
        }.get(lvl, "lvl-info")
        lines.append(f"<div class='logline {cls}'>{lvl:<4} {msg}</div>")
    st.markdown("<div class='logbox'>" + "".join(lines) + "</div>", unsafe_allow_html=True)


def _scan_wifi():
    if not HAS_WIFI:
        return []
    try:
        wifi = PyWiFi()
        ifaces = wifi.interfaces()
        if not ifaces:
            return []
        iface = ifaces[0]
        iface.scan()
        time.sleep(0.7)
        results = iface.scan_results()
        networks = []
        seen = set()
        for r in results:
            ssid = r.ssid or "<hidden>"
            if ssid in seen:
                continue
            seen.add(ssid)
            networks.append({"ssid": ssid, "signal": r.signal})
        return networks
    except Exception:
        return []


def _fig_radar(max_r: float) -> go.Figure:
    """Neon askeri radar görünümü: grid, sweep ve Wi‑Fi hedefleri."""
    nets = st.session_state.wifi_networks

    if not nets:
        nets = [
            {"ssid": "HIVE-NODE-A", "signal": -45},
            {"ssid": "HIVE-NODE-B", "signal": -60},
            {"ssid": "RescueMesh", "signal": -72},
        ]

    n = len(nets)
    angles = np.linspace(0, 360, n, endpoint=False) if n > 0 else [0]
    rssi_vals = np.array([net["signal"] for net in nets], dtype=float)

    min_rssi, max_rssi = -90.0, -30.0
    rssi_clipped = np.clip(rssi_vals, min_rssi, max_rssi)
    norm = (rssi_clipped - max_rssi) / (min_rssi - max_rssi)
    radii = max_r * (0.2 + 0.8 * norm)

    sizes = [14 + (1.0 - n_) * 12 for n_ in norm]
    colors = [NEON_LIME for _ in rssi_vals]
    hover = [
        f"{net['ssid']}<br>RSSI: {sig:.0f} dBm<br>Range: {r:.1f} m"
        for net, sig, r in zip(nets, rssi_vals, radii)
    ]

    fig = go.Figure()

    # Radar tarama çizgisi (sweep)
    sweep_angle = (st.session_state.tick * 8) % 360
    sweep_width = 35
    sweep_thetas = np.linspace(sweep_angle - sweep_width / 2, sweep_angle + sweep_width / 2, 40)
    sweep_r = np.linspace(0, max_r, 40)
    sweep_rr, sweep_tt = np.meshgrid(sweep_r, sweep_thetas)

    fig.add_trace(
        go.Scatterpolar(
            r=sweep_rr.flatten(),
            theta=sweep_tt.flatten(),
            mode="markers",
            marker=dict(
                size=2,
                color="rgba(166,255,0,0.16)",
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Dairesel gridler
    for rr in np.linspace(2, max_r, int(max_r // 2)):
        fig.add_trace(
            go.Scatterpolar(
                r=[rr] * 361,
                theta=list(range(361)),
                mode="lines",
                line=dict(color="rgba(0,255,100,0.25)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # Hedef noktalar (Wi‑Fi ağları)
    fig.add_trace(
        go.Scatterpolar(
            r=radii.tolist(),
            theta=angles.tolist(),
            mode="markers",
            marker=dict(
                size=sizes,
                color=colors,
                symbol="cross",
                line=dict(color="rgba(0,0,0,0.85)", width=1.2),
            ),
            text=hover,
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG,
        margin=dict(l=16, r=16, t=20, b=10),
        font=dict(color=NEON_LIME),
        polar=dict(
            bgcolor="#020806",
            radialaxis=dict(range=[0, max_r], showticklabels=False, ticks="", gridcolor="rgba(0,255,100,0.35)"),
            angularaxis=dict(showticklabels=False, ticks="", gridcolor="rgba(0,255,100,0.15)"),
        ),
    )
    return fig


def _fft_from_microphone(
    sample_rate: int = 16_000, duration: float = 0.12
):
    if not HAS_SOUND:
        raise RuntimeError("Ses cihazı modülü yüklenemedi.")
    try:
        n_samples = int(sample_rate * duration)
        audio = sd.rec(
            n_samples,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        audio = np.squeeze(audio)
        if audio.size == 0:
            raise RuntimeError("Boş ses verisi.")
        window = np.hanning(audio.size)
        audio_win = audio * window
        spectrum_complex = np.fft.rfft(audio_win)
        spectrum = np.abs(spectrum_complex)
        freqs = np.fft.rfftfreq(audio_win.size, 1.0 / sample_rate)
        if np.max(spectrum) > 0:
            spectrum = spectrum / np.max(spectrum)
        peak_level = float(np.max(spectrum))
        return freqs, spectrum, peak_level, True
    except Exception as e:
        raise RuntimeError(str(e))


def _fft_simulated(n_bins: int = 160):
    f = np.linspace(0, 4000, n_bins)
    peaks = [
        (150 + 40 * np.sin(st.session_state.tick / 7), 0.9),
        (450 + 60 * np.cos(st.session_state.tick / 11), 0.6),
        (1200 + 120 * np.sin(st.session_state.tick / 13), 0.5),
        (2400 + 150 * np.cos(st.session_state.tick / 9), 0.35),
    ]
    a = np.zeros_like(f, dtype=float)
    for center, amp in peaks:
        a += amp * np.exp(-0.5 * ((f - center) / (70 + 25 * np.random.rand())) ** 2)
    a += 0.08 * np.random.rand(n_bins)
    a = np.clip(a, 0, 1.0)
    peak_level = float(np.max(a))
    return f, a, peak_level, False


def _fig_fft_live():
    try:
        freqs, spectrum, peak_level, is_real = _fft_from_microphone()
    except Exception:
        freqs, spectrum, peak_level, is_real = _fft_simulated()

    df = pd.DataFrame({"Hz": freqs, "Amp": spectrum})

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
            line=dict(color=NEON_LIME, width=1.6),
            opacity=0.9,
            hoverinfo="skip",
            name="Smoothed",
        )
    )

    fig.update_layout(
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG,
        margin=dict(l=16, r=16, t=20, b=10),
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
    return fig, peak_level, is_real


_ensure_state()

with st.sidebar:
    st.markdown("### HIVE-MAP | Control")
    live = st.toggle("Live Simulation", value=True)
    fps = st.slider("Refresh rate (FPS)", min_value=2, max_value=12, value=6, step=1)
    radar_range = st.slider("Radar range (m)", min_value=8, max_value=20, value=12, step=1)

st.markdown("<div class='cy-title' style='font-size:34px'>HIVE-MAP // CYBER COMMAND</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='cy-sub'>AFAD / JAK Mobil Operasyon Arayüzü • <span class='cy-badge'>DARK • NEON • REAL-TIME</span></div>",
    unsafe_allow_html=True,
)

top_left, top_right = st.columns(2, gap="large")

with top_left:
    st.markdown("<div class='cy-panel'>", unsafe_allow_html=True)
    st.subheader("📡 Taktik Neon Radar (Wi‑Fi RSSI)")
    radar_chart = st.empty()
    st.caption("Çevresel Wi‑Fi ağları • RSSI → menzil/yoğunluk (pywifi ile tarama)")
    radar_logs = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

with top_right:
    st.markdown("<div class='cy-panel'>", unsafe_allow_html=True)
    st.subheader("🎙️ Akustik Spektrum Analizi (Real‑Time FFT)")
    audio_alert = st.empty()
    audio_chart = st.empty()
    st.caption("Mikrofon verisi (mümkünse) + simülasyon; ses eşiği aşılırsa uyarı üretir.")
    audio_logs = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

st.markdown("<div class='cy-panel'>", unsafe_allow_html=True)
st.subheader("📊 Telemetri")
m1, m2, m3, m4 = st.columns(4, gap="large")
telemetry_logs = st.empty()
st.markdown("</div>", unsafe_allow_html=True)


def _render_frame():
    st.session_state.tick += 1

    # Wi‑Fi taraması (gerçek veri, mümkünse)
    if st.session_state.tick - st.session_state.last_wifi_scan_tick >= 10:
        nets = _scan_wifi()
        if nets:
            st.session_state.wifi_networks = nets
            st.session_state.last_wifi_scan_tick = st.session_state.tick
            _push_log("radar", "OK", f"{len(nets)} Wi‑Fi ağı tarandı.")
        elif not st.session_state.wifi_networks:
            _push_log("radar", "WARN", "Yakındaki Wi‑Fi ağları okunamadı, radar demo modunda.")

    if st.session_state.tick % 2 == 0:
        _push_log("radar", "INFO", "Sinyal taranıyor...")
    if st.session_state.tick % 5 == 0:
        _push_log("radar", "OK", "Beacon paketleri çözümlendi (BLE ADV).")
    if st.session_state.tick % 7 == 0:
        _push_log("audio", "INFO", "Frekans aralığı analiz ediliyor...")
    if st.session_state.tick % 11 == 0:
        _push_log("audio", "OK", "Spektral tepe noktaları güncellendi.")
    if st.session_state.tick % 13 == 0:
        _push_log("telemetry", "WARN", "Kısa süreli parazit algılandı, filtre uygulanıyor.")
    if st.session_state.tick % 17 == 0:
        _push_log("telemetry", "OK", "Bağlantı kararlı (paket kaybı düşük).")

    radar_chart.plotly_chart(_fig_radar(radar_range), use_container_width=True, config={"displayModeBar": False})
    radar_logs.container()
    with radar_logs:
        _render_logs("radar")

    fig_audio, peak_level, is_real = _fig_fft_live()
    audio_chart.plotly_chart(fig_audio, use_container_width=True, config={"displayModeBar": False})

    # Ses eşiği kontrolü
    AUDIO_THRESHOLD = 0.45
    if peak_level > AUDIO_THRESHOLD:
        st.session_state.last_audio_alert_tick = st.session_state.tick
        _push_log("audio", "WARN", "SES TESPİT EDİLDİ – eşik aşıldı.")

    if st.session_state.tick - st.session_state.last_audio_alert_tick <= 12:
        audio_alert.markdown(
            "<div style='padding:6px 10px;margin-bottom:6px;border-radius:10px;"
            "background:rgba(255,0,80,0.18);border:1px solid rgba(255,0,80,0.75);"
            "color:#FFECEC;font-weight:800;text-align:center;letter-spacing:1.2px;'>"
            "SES TESPİT EDİLDİ</div>",
            unsafe_allow_html=True,
        )
    else:
        audio_alert.empty()
    audio_logs.container()
    with audio_logs:
        _render_logs("audio")

    detected = len(st.session_state.wifi_networks) if st.session_state.wifi_networks else 3
    link_quality = int(np.clip(92 + 4 * np.sin(st.session_state.tick / 8) + np.random.normal(0, 1.2), 72, 99))
    battery = int(np.clip(86 - (st.session_state.tick % 240) * 0.08 + np.random.normal(0, 0.6), 18, 99))
    noise_gate = int(np.clip(65 + 12 * np.cos(st.session_state.tick / 10) + np.random.normal(0, 2.0), 35, 90))

    m1.metric("Tespit Edilen Cihaz", detected, delta="Aktif tarama")
    m2.metric("Bağlantı Kalitesi", f"%{link_quality}", delta="Mesh uplink")
    m3.metric("Batarya", f"%{battery}", delta="Nominal")
    m4.metric("Gürültü Bastırma", f"%{noise_gate}", delta="Band-pass + gate")

    telemetry_logs.container()
    with telemetry_logs:
        _render_logs("telemetry")


if live:
    frames = int(8 * fps)  # ~8 saniyelik canlı akış
    for _ in range(frames):
        _render_frame()
        time.sleep(1 / fps)
else:
    _render_frame()

st.caption("İpucu: Sol menüden FPS ve cihaz sayısını artırıp demo etkisini güçlendirebilirsin.")