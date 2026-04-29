from flask import Flask, jsonify, render_template_string, request
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

WINDOW_MAP = {
    "10m": timedelta(minutes=10),
    "30m": timedelta(minutes=30),
    "1h":  timedelta(hours=1),
    "6h":  timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d":  timedelta(days=7),
}
MAX_POINTS = 200

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Weather Station</title>
  <link href="https://fonts.googleapis.com/css2?family=Martian+Mono:wght@300;400;600&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
  <style>
    :root {
      --bg:       #080c12;
      --surface:  #0e1420;
      --border:   #1c2535;
      --temp:     #f5a623;
      --temp-dim: rgba(245,166,35,0.12);
      --hum:      #00c9ff;
      --hum-dim:  rgba(0,201,255,0.10);
      --dp:       #a78bfa;
      --hi:       #fb7185;
      --text:     #cdd6e0;
      --muted:    #4a5568;
      --live:     #3effa0;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg);
      background-image: radial-gradient(var(--border) 1px, transparent 1px);
      background-size: 28px 28px;
      color: var(--text);
      font-family: 'Outfit', sans-serif;
      min-height: 100vh;
      padding: 48px 24px;
    }

    @keyframes fadeUp {
      from { opacity:0; transform:translateY(16px); }
      to   { opacity:1; transform:translateY(0); }
    }

    .container { max-width: 900px; margin: 0 auto; animation: fadeUp 0.6s ease both; }

    header {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 32px;
      flex-wrap: wrap;
    }

    header h1 {
      font-family: 'Martian Mono', monospace;
      font-size: 1.1rem;
      font-weight: 400;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .live-dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: var(--live);
      box-shadow: 0 0 8px var(--live);
      animation: pulse 2s ease-in-out infinite;
      flex-shrink: 0;
    }

    @keyframes pulse {
      0%,100% { opacity:1; box-shadow:0 0 6px var(--live); }
      50%     { opacity:0.4; box-shadow:0 0 2px var(--live); }
    }

    .last-updated {
      margin-left: auto;
      font-family: 'Martian Mono', monospace;
      font-size: 0.65rem;
      color: var(--muted);
      letter-spacing: 0.05em;
    }

    /* Time window selector */
    .window-bar {
      display: flex;
      gap: 8px;
      margin-bottom: 24px;
    }

    .win-btn {
      font-family: 'Martian Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 3px;
      color: var(--muted);
      padding: 6px 14px;
      cursor: pointer;
      transition: all 0.15s;
    }

    .win-btn:hover { border-color: var(--text); color: var(--text); }
    .win-btn.active { border-color: var(--live); color: var(--live); }

    /* Cards */
    .cards {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr 1fr;
      gap: 12px;
      margin-bottom: 20px;
    }

    @media (max-width: 700px) { .cards { grid-template-columns: 1fr 1fr; } }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 20px 24px;
      position: relative;
      overflow: hidden;
      animation: fadeUp 0.6s ease both;
    }

    .card.temp { border-top: 2px solid var(--temp); animation-delay:0.1s; }
    .card.hum  { border-top: 2px solid var(--hum);  animation-delay:0.2s; }
    .card.dp   { border-top: 2px solid var(--dp);   animation-delay:0.3s; }
    .card.hi   { border-top: 2px solid var(--hi);   animation-delay:0.4s; }

    .card::after { content:''; position:absolute; inset:0; pointer-events:none; }
    .card.temp::after { background: var(--temp-dim); }
    .card.hum::after  { background: var(--hum-dim); }
    .card.dp::after   { background: rgba(167,139,250,0.07); }
    .card.hi::after   { background: rgba(251,113,133,0.07); }

    .card-label {
      font-family: 'Martian Mono', monospace;
      font-size: 0.58rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 10px;
    }

    .roller {
      display: flex;
      align-items: flex-end;
      gap: 1px;
      height: 2.8rem;
      overflow: hidden;
      font-family: 'Martian Mono', monospace;
      font-size: 2.6rem;
      font-weight: 300;
      line-height: 1;
    }

    .card.temp .roller { color: var(--temp); }
    .card.hum  .roller { color: var(--hum); }
    .card.dp   .roller { color: var(--dp); }
    .card.hi   .roller { color: var(--hi); }

    .digit-slot { position:relative; height:2.8rem; overflow:hidden; }
    .digit-inner {
      display:flex; flex-direction:column;
      transition: transform 0.45s cubic-bezier(0.25,0.8,0.25,1);
    }
    .digit-inner span {
      height:2.8rem;
      display:flex; align-items:center; justify-content:center;
    }

    .card-unit {
      font-family: 'Martian Mono', monospace;
      font-size: 0.7rem;
      color: var(--muted);
      margin-top: 6px;
      letter-spacing: 0.08em;
    }

    /* Charts */
    .chart-block {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 24px 28px;
      margin-bottom: 14px;
      animation: fadeUp 0.6s ease both;
    }

    .chart-block:nth-child(1) { animation-delay:0.5s; }
    .chart-block:nth-child(2) { animation-delay:0.6s; }

    .chart-header {
      display:flex; align-items:center;
      gap:10px; margin-bottom:16px;
    }

    .chart-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
    .chart-dot.temp { background: var(--temp); }
    .chart-dot.hum  { background: var(--hum); }

    .chart-title {
      font-family: 'Martian Mono', monospace;
      font-size: 0.62rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
    }

    .minmax-legend {
      margin-left: auto;
      display: flex;
      gap: 14px;
      font-family: 'Martian Mono', monospace;
      font-size: 0.6rem;
      color: var(--muted);
    }

    .minmax-legend span { display:flex; align-items:center; gap:5px; }
    .minmax-legend i {
      display:inline-block; width:16px; height:1px;
      border-top: 1px dashed;
    }
    .minmax-legend .max-line i { border-color: rgba(255,255,255,0.4); }
    .minmax-legend .min-line i { border-color: rgba(255,255,255,0.2); }
  </style>
</head>
<body>
<div class="container">
  <header>
    <div class="live-dot"></div>
    <h1>Weather Station</h1>
    <span class="last-updated" id="updated">--</span>
  </header>

  <div class="window-bar">
    <button class="win-btn" data-w="10m">10 min</button>
    <button class="win-btn" data-w="30m">30 min</button>
    <button class="win-btn active" data-w="1h">1 hour</button>
    <button class="win-btn" data-w="6h">6 hours</button>
    <button class="win-btn" data-w="24h">24 hours</button>
    <button class="win-btn" data-w="7d">7 days</button>
  </div>

  <div class="cards">
    <div class="card temp">
      <div class="card-label">Temperature</div>
      <div class="roller" id="tempRoller"></div>
      <div class="card-unit">°C</div>
    </div>
    <div class="card hum">
      <div class="card-label">Humidity</div>
      <div class="roller" id="humRoller"></div>
      <div class="card-unit">% RH</div>
    </div>
    <div class="card dp">
      <div class="card-label">Dew Point</div>
      <div class="roller" id="dpRoller"></div>
      <div class="card-unit">°C</div>
    </div>
    <div class="card hi">
      <div class="card-label">Heat Index</div>
      <div class="roller" id="hiRoller"></div>
      <div class="card-unit">°C feels-like</div>
    </div>
  </div>

  <div class="chart-block">
    <div class="chart-header">
      <div class="chart-dot temp"></div>
      <span class="chart-title">Temperature — °C</span>
      <div class="minmax-legend">
        <span class="max-line"><i></i>max</span>
        <span class="min-line"><i></i>min</span>
      </div>
    </div>
    <canvas id="tempChart" height="90"></canvas>
  </div>

  <div class="chart-block">
    <div class="chart-header">
      <div class="chart-dot hum"></div>
      <span class="chart-title">Humidity — % RH</span>
      <div class="minmax-legend">
        <span class="max-line"><i></i>max</span>
        <span class="min-line"><i></i>min</span>
      </div>
    </div>
    <canvas id="humChart" height="90"></canvas>
  </div>
</div>

<script>
  Chart.register(window['chartjs-plugin-annotation']);

  // ── Digit Roller ─────────────────────────────────────────────────────────
  const DIGITS = '0123456789.-';

  function buildRoller(id) {
    const el = document.getElementById(id);
    el._slots = [];
    el._current = '';
    return el;
  }

  function setRollerValue(el, str) {
    if (el._current === str) return;
    el._current = str;
    const chars = str.split('');

    while (el._slots.length < chars.length) {
      const slot = document.createElement('div');
      slot.className = 'digit-slot';
      const inner = document.createElement('div');
      inner.className = 'digit-inner';
      DIGITS.split('').forEach(d => {
        const span = document.createElement('span');
        span.textContent = d;
        inner.appendChild(span);
      });
      slot.appendChild(inner);
      el.appendChild(slot);
      el._slots.push({ slot, inner });
    }

    while (el._slots.length > chars.length) {
      const r = el._slots.pop();
      el.removeChild(r.slot);
    }

    chars.forEach((ch, i) => {
      const idx = DIGITS.indexOf(ch);
      if (idx < 0) return;
      setTimeout(() => {
        el._slots[i].inner.style.transform = `translateY(-${idx * 2.8}rem)`;
      }, i * 40);
    });
  }

  const tempRoller = buildRoller('tempRoller');
  const humRoller  = buildRoller('humRoller');
  const dpRoller   = buildRoller('dpRoller');
  const hiRoller   = buildRoller('hiRoller');

  // ── Crosshair Plugin ─────────────────────────────────────────────────────
  const crosshairPlugin = {
    id: 'crosshair',
    afterDraw(chart) {
      if (!chart._active?.length) return;
      const ctx = chart.ctx;
      const x = chart._active[0].element.x;
      const { top, bottom } = chart.chartArea;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, bottom);
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(255,255,255,0.15)';
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.restore();
    }
  };

  Chart.register(crosshairPlugin);

  // ── Chart factory ─────────────────────────────────────────────────────────
  function makeChart(canvasId, color, unit, extraOpts = {}) {
    return new Chart(document.getElementById(canvasId).getContext('2d'), {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          data: [],
          borderColor: color,
          backgroundColor: color.replace(')', ',0.08)').replace('rgb', 'rgba'),
          borderWidth: 1.5,
          spanGaps: false,
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBorderWidth: 2,
          pointHoverBackgroundColor: '#080c12',
          pointHoverBorderColor: color,
        },
        {
          // Gap connectors — dashed lines drawn only across data gaps
          data: [],
          spanGaps: false,
          borderColor: color,
          borderWidth: 1,
          borderDash: [5, 7],
          fill: false,
          tension: 0,
          pointRadius: 0,
          pointHoverRadius: 0,
        }]
      },
      options: {
        responsive: true,
        animation: { duration: 400 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0e1420',
            borderColor: '#1c2535',
            borderWidth: 1,
            titleColor: '#4a5568',
            bodyColor: color,
            titleFont: { family: 'Martian Mono', size: 9 },
            bodyFont:  { family: 'Martian Mono', size: 13 },
            padding: 12,
            displayColors: false,
            callbacks: {
              title: items => {
                if (!items.length) return '';
                return new Date(items[0].parsed.x)
                  .toLocaleTimeString('en-CA', { hour12: false });
              },
              label: item => {
                if (item.datasetIndex !== 0 || item.raw?.y === null) return null;
                return `${parseFloat(item.raw.y).toFixed(1)} ${unit}`;
              }
            }
          },
          annotation: { annotations: {} }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              displayFormats: {
                millisecond: 'HH:mm:ss',
                second:      'HH:mm:ss',
                minute:      'HH:mm',
                hour:        'HH:mm',
                day:         'MMM d',
              }
            },
            ticks: { color:'#4a5568', font:{family:'Martian Mono',size:9}, maxTicksLimit:8 },
            grid:  { color:'#1c2535' }
          },
          y: {
            ticks: { color:'#4a5568', font:{family:'Martian Mono',size:9} },
            grid:  { color:'#1c2535' },
            grace: '10%',
            ...extraOpts
          }
        }
      }
    });
  }

  const tempChart = makeChart('tempChart', '#f5a623', '°C');
  const humChart  = makeChart('humChart',  '#00c9ff', '% RH', { min: 0, max: 100 });

  function setMinMaxAnnotations(chart, values) {
    if (!values.length) return;
    const min = Math.min(...values);
    const max = Math.max(...values);
    chart.options.plugins.annotation.annotations = {
      maxLine: {
        type: 'line', yMin: max, yMax: max,
        borderColor: 'rgba(255,255,255,0.35)',
        borderWidth: 1, borderDash: [5, 5],
        label: {
          display: true,
          content: `max ${max.toFixed(1)}`,
          position: 'end',
          backgroundColor: 'transparent',
          color: 'rgba(255,255,255,0.35)',
          font: { family: 'Martian Mono', size: 9 }
        }
      },
      minLine: {
        type: 'line', yMin: min, yMax: min,
        borderColor: 'rgba(255,255,255,0.18)',
        borderWidth: 1, borderDash: [5, 5],
        label: {
          display: true,
          content: `min ${min.toFixed(1)}`,
          position: 'end',
          backgroundColor: 'transparent',
          color: 'rgba(255,255,255,0.18)',
          font: { family: 'Martian Mono', size: 9 }
        }
      }
    };
    chart.update();
  }

  // ── Time window ───────────────────────────────────────────────────────────
  let currentWindow = '1h';

  document.querySelectorAll('.win-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.win-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentWindow = btn.dataset.w;
      update();
    });
  });

  // ── Gap detection + series builder ─────────────────────────────────────────
  // Returns {main, gaps} — both arrays of {x: Date, y: value|null}.
  // main: solid line with null breaks at gap positions (time-proportional x).
  // gaps: dashed connector segments drawn only across gap regions.
  const GAP_FACTOR = 3;

  function buildSeriesData(rows, field) {
    if (!rows.length) return { main: [], gaps: [] };
    if (rows.length === 1)
      return { main: [{ x: new Date(rows[0].timestamp), y: rows[0][field] }], gaps: [] };

    const intervals = [];
    for (let i = 1; i < rows.length; i++)
      intervals.push(new Date(rows[i].timestamp) - new Date(rows[i-1].timestamp));
    intervals.sort((a, b) => a - b);
    const threshold = intervals[Math.floor(intervals.length / 2)] * GAP_FACTOR;

    const main = [];
    const gaps = [];

    main.push({ x: new Date(rows[0].timestamp), y: rows[0][field] });

    for (let i = 1; i < rows.length; i++) {
      const dt  = new Date(rows[i].timestamp);
      const gap = dt - new Date(rows[i-1].timestamp);

      if (gap > threshold) {
        // Break the solid line at this timestamp
        main.push({ x: dt, y: null });

        // Dashed connector: last real point → next real point.
        // Separate multiple gap segments with a null-y midpoint.
        if (gaps.length > 0) {
          const prev = gaps[gaps.length - 1];
          const mid  = new Date((prev.x.getTime() + new Date(rows[i-1].timestamp).getTime()) / 2);
          gaps.push({ x: mid, y: null });
        }
        gaps.push({ x: new Date(rows[i-1].timestamp), y: rows[i-1][field] });
        gaps.push({ x: dt,                            y: rows[i][field]   });
      }

      main.push({ x: dt, y: rows[i][field] });
    }

    return { main, gaps };
  }

  // ── Update loop ───────────────────────────────────────────────────────────
  async function update() {
    const res = await fetch('/data?window=' + currentWindow);
    const raw = await res.json();
    if (!raw.length) return;

    const latest = raw[raw.length - 1];
    setRollerValue(tempRoller, parseFloat(latest.temperature).toFixed(1));
    setRollerValue(humRoller,  parseFloat(latest.humidity).toFixed(1));
    setRollerValue(dpRoller,   parseFloat(latest.dew_point ?? 0).toFixed(1));
    setRollerValue(hiRoller,   parseFloat(latest.heat_index ?? 0).toFixed(1));
    document.getElementById('updated').textContent = 'last — ' + latest.timestamp.slice(11,19);

    const tempSeries = buildSeriesData(raw, 'temperature');
    const humSeries  = buildSeriesData(raw, 'humidity');

    tempChart.data.datasets[0].data = tempSeries.main;
    tempChart.data.datasets[1].data = tempSeries.gaps;
    tempChart.update();
    setMinMaxAnnotations(tempChart, tempSeries.main.filter(p => p.y !== null).map(p => p.y));

    humChart.data.datasets[0].data = humSeries.main;
    humChart.data.datasets[1].data = humSeries.gaps;
    humChart.update();
    setMinMaxAnnotations(humChart, humSeries.main.filter(p => p.y !== null).map(p => p.y));
  }

  update();
  setInterval(update, 5000);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/data")
def data():
    window = request.args.get("window", "1h")
    delta  = WINDOW_MAP.get(window, timedelta(hours=1))
    since  = (datetime.now() - delta).isoformat()

    conn = sqlite3.connect("weather.db")
    rows = conn.execute(
        """SELECT timestamp, temperature, humidity, dew_point, heat_index
           FROM readings WHERE timestamp >= ? ORDER BY id ASC""",
        (since,)
    ).fetchall()
    conn.close()

    if len(rows) > MAX_POINTS:
        step = max(1, len(rows) // MAX_POINTS)
        rows = rows[::step]

    return jsonify([{
        "timestamp":   r[0],
        "temperature": r[1],
        "humidity":    r[2],
        "dew_point":   r[3],
        "heat_index":  r[4],
    } for r in rows])

if __name__ == "__main__":
    app.run(debug=True)