import { useState, useMemo } from 'react'
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine, ReferenceArea
} from 'recharts'

// wjsi_with_pt = reference 6-component variant (includes pt_econ)
const WITH_PT = {"2001":94.57,"2002":93.654,"2003":89.873,"2004":95.72,"2005":100.0,"2006":102.461,"2007":99.296,"2008":88.612,"2009":62.27,"2010":72.619,"2011":76.357,"2012":80.771,"2013":87.181,"2014":92.347,"2015":92.5,"2016":92.796,"2017":97.667,"2018":98.733,"2019":100.78,"2020":48.653,"2021":100.441,"2022":103.668,"2023":96.635,"2024":91.892,"2025":97.702}

// Primary WJSI: 5-component (with pt_econ) — pt_econ excluded due to structural overlap with U-6
const RAW = [{"year":2001,"wjsi":89.769,"u6":8.15,"michigan":89.242,"conference_board":100.422,"unrate":4.742,"savings_rate":4.675,"real_gdp_growth":1.0},{"year":2002,"wjsi":92.075,"u6":9.592,"michigan":89.583,"conference_board":100.413,"unrate":5.783,"savings_rate":5.575,"real_gdp_growth":1.7},{"year":2003,"wjsi":90.341,"u6":10.125,"michigan":87.625,"conference_board":100.256,"unrate":5.992,"savings_rate":5.192,"real_gdp_growth":2.8},{"year":2004,"wjsi":96.519,"u6":9.592,"michigan":95.2,"conference_board":101.071,"unrate":5.542,"savings_rate":4.65,"real_gdp_growth":3.8},{"year":2005,"wjsi":100.0,"u6":8.925,"michigan":88.55,"conference_board":100.318,"unrate":5.083,"savings_rate":2.25,"real_gdp_growth":3.5},{"year":2006,"wjsi":101.345,"u6":8.233,"michigan":87.308,"conference_board":100.187,"unrate":4.608,"savings_rate":2.775,"real_gdp_growth":2.8},{"year":2007,"wjsi":98.562,"u6":8.333,"michigan":85.583,"conference_board":99.974,"unrate":4.617,"savings_rate":2.525,"real_gdp_growth":2.0},{"year":2008,"wjsi":94.762,"u6":10.55,"michigan":63.75,"conference_board":97.379,"unrate":5.8,"savings_rate":4.133,"real_gdp_growth":0.1},{"year":2009,"wjsi":83.191,"u6":16.258,"michigan":66.258,"conference_board":97.694,"unrate":9.283,"savings_rate":5.733,"real_gdp_growth":-2.6},{"year":2010,"wjsi":96.466,"u6":16.742,"michigan":71.842,"conference_board":98.342,"unrate":9.608,"savings_rate":5.925,"real_gdp_growth":2.7},{"year":2011,"wjsi":98.768,"u6":15.933,"michigan":67.35,"conference_board":97.831,"unrate":8.933,"savings_rate":6.55,"real_gdp_growth":1.6},{"year":2012,"wjsi":100.404,"u6":14.683,"michigan":76.542,"conference_board":98.89,"unrate":8.075,"savings_rate":7.858,"real_gdp_growth":2.3},{"year":2013,"wjsi":106.808,"u6":13.792,"michigan":79.208,"conference_board":99.217,"unrate":7.358,"savings_rate":4.967,"real_gdp_growth":2.1},{"year":2014,"wjsi":107.89,"u6":12.033,"michigan":84.125,"conference_board":99.805,"unrate":6.158,"savings_rate":5.467,"real_gdp_growth":2.5},{"year":2015,"wjsi":101.936,"u6":10.45,"michigan":92.942,"conference_board":100.822,"unrate":5.275,"savings_rate":5.85,"real_gdp_growth":2.9},{"year":2016,"wjsi":98.912,"u6":9.625,"michigan":91.842,"conference_board":100.707,"unrate":4.875,"savings_rate":5.358,"real_gdp_growth":1.8},{"year":2017,"wjsi":100.372,"u6":8.517,"michigan":96.767,"conference_board":101.289,"unrate":4.358,"savings_rate":5.758,"real_gdp_growth":2.5},{"year":2018,"wjsi":98.349,"u6":7.725,"michigan":98.367,"conference_board":101.453,"unrate":3.892,"savings_rate":6.433,"real_gdp_growth":3.0},{"year":2019,"wjsi":98.398,"u6":7.15,"michigan":95.983,"conference_board":101.234,"unrate":3.675,"savings_rate":7.308,"real_gdp_growth":2.6},{"year":2020,"wjsi":51.733,"u6":13.667,"michigan":81.542,"conference_board":99.465,"unrate":8.1,"savings_rate":15.092,"real_gdp_growth":-2.1},{"year":2021,"wjsi":101.982,"u6":9.408,"michigan":77.617,"conference_board":99.035,"unrate":5.35,"savings_rate":11.325,"real_gdp_growth":6.2},{"year":2022,"wjsi":99.1,"u6":6.875,"michigan":58.975,"conference_board":96.855,"unrate":3.65,"savings_rate":3.35,"real_gdp_growth":2.5},{"year":2023,"wjsi":90.544,"u6":6.883,"michigan":65.35,"conference_board":97.586,"unrate":3.625,"savings_rate":5.592,"real_gdp_growth":2.9},{"year":2024,"wjsi":86.784,"u6":7.525,"michigan":72.542,"conference_board":98.913,"unrate":4.025,"savings_rate":5.433,"real_gdp_growth":2.8},{"year":2025,"wjsi":93.431,"u6":7.991,"michigan":57.583,"conference_board":null,"unrate":4.264,"savings_rate":4.633,"real_gdp_growth":2.1}]

const SERIES_META = {
  u6:               { label: 'U-6 Underemployment',  color: '#e74c3c', defaultInvert: true,  description: 'Broadest unemployment measure — includes part-time + marginally attached' },
  michigan:         { label: 'Michigan Sentiment',   color: '#9b59b6', defaultInvert: false, description: 'University of Michigan Consumer Sentiment Index' },
  conference_board: { label: 'Conference Board',     color: '#3498db', defaultInvert: false, description: 'Conference Board Consumer Confidence Index' },
  unrate:           { label: 'U-3 Unemployment',     color: '#e67e22', defaultInvert: true,  description: 'Official BLS headline unemployment rate' },
  savings_rate:     { label: 'Personal Saving Rate', color: '#27ae60', defaultInvert: true,  description: 'Personal saving as % of disposable income — rises with precautionary fear' },
  real_gdp_growth:  { label: 'Real GDP Growth',      color: '#1abc9c', defaultInvert: false, description: 'Annual real GDP growth rate' },
}

const RECESSIONS = [
  { start: 2001, end: 2001, label: 'Dot-com' },
  { start: 2008, end: 2009, label: 'GFC' },
  { start: 2020, end: 2020, label: 'COVID' },
]

function pearson(xs, ys) {
  const n = xs.length
  if (n < 3) return null
  const mx = xs.reduce((a, b) => a + b, 0) / n
  const my = ys.reduce((a, b) => a + b, 0) / n
  let num = 0, dx2 = 0, dy2 = 0
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - mx, dy = ys[i] - my
    num += dx * dy; dx2 += dx * dx; dy2 += dy * dy
  }
  return dx2 === 0 || dy2 === 0 ? null : num / Math.sqrt(dx2 * dy2)
}

function normalise(vals) {
  const clean = vals.filter(v => v != null && isFinite(v))
  if (!clean.length) return vals.map(() => null)
  const min = Math.min(...clean), max = Math.max(...clean)
  if (max === min) return vals.map(v => v == null ? null : 50)
  return vals.map(v => v == null ? null : ((v - min) / (max - min)) * 100)
}

function CorrBadge({ r, n, label, lag }) {
  if (r == null) return <div style={{ color: '#555', fontSize: 13 }}>Insufficient data</div>
  const abs = Math.abs(r)
  const color = abs > 0.85 ? '#e74c3c' : abs > 0.6 ? '#f39c12' : '#2ecc71'
  return (
    <div style={{ background: '#0c0c18', border: `2px solid ${color}`, borderRadius: 10, padding: '14px 16px' }}>
      <div style={{ fontSize: 34, fontWeight: 700, color, letterSpacing: -1, lineHeight: 1 }}>r = {r.toFixed(3)}</div>
      <div style={{ color: '#777', fontSize: 12, marginTop: 6 }}>
        {abs > 0.85 ? 'Strong' : abs > 0.6 ? 'Meaningful' : 'Weak'} {r < 0 ? 'inverse' : 'positive'} · n={n}
      </div>
      {lag !== 0 && (
        <div style={{ color: '#4fc3f7', fontSize: 12, marginTop: 5 }}>
          {lag > 0 ? `WJSI leads by ${lag}yr` : `${label} leads WJSI by ${Math.abs(lag)}yr`}
        </div>
      )}
      {abs > 0.85 && <div style={{ color: '#e74c3c', fontSize: 11, marginTop: 6 }}>⚠ Potential redundancy</div>}
      {abs < 0.5 && <div style={{ color: '#2ecc71', fontSize: 11, marginTop: 6 }}>✓ Measures something distinct</div>}
    </div>
  )
}

function CustomTooltip({ active, payload, label, compLabel, lag, inverted }) {
  if (!active || !payload?.length) return null
  const w = payload.find(p => p.dataKey === 'wjsi')
  const c = payload.find(p => p.dataKey === 'comp')
  return (
    <div style={{ background: '#1a1a2e', border: '1px solid #333', borderRadius: 8, padding: '10px 14px', fontSize: 13 }}>
      <div style={{ color: '#777', marginBottom: 5, fontWeight: 600 }}>{label}</div>
      {w && <div style={{ color: '#4fc3f7' }}>WJSI: <b>{w.value?.toFixed(1)}</b></div>}
      {c && <div style={{ color: c.stroke }}>
        {compLabel}{inverted ? ' (inv)' : ''}{lag !== 0 ? ` [${lag > 0 ? '+' : ''}${lag}yr]` : ''}: <b>{c.value?.toFixed(1)}</b>
      </div>}
    </div>
  )
}

export default function App() {
  const [selectedKey, setSelectedKey] = useState('u6')
  const [lag, setLag] = useState(0)
  const [invertComp, setInvertComp] = useState(true)
  const [normalised, setNormalised] = useState(true)
  const [showNopt, setShowNopt] = useState(true)

  const meta = SERIES_META[selectedKey]

  // Enrich RAW with nopt values
  const RAWX = useMemo(() => RAW.map(d => ({ ...d, wjsi_with_pt: WITH_PT[String(d.year)] ?? null })), [])

  const chartData = useMemo(() => {
    const ym = Object.fromEntries(RAWX.map(d => [d.year, d]))
    return RAWX.map(d => {
      const raw = ym[d.year + lag]?.[selectedKey] ?? null
      const comp = raw == null ? null : (invertComp ? -raw : raw)
      return { year: d.year, wjsiRaw: d.wjsi, wjsiNopt: d.wjsi_with_pt, compRaw: comp }
    })
  }, [selectedKey, lag, invertComp, RAWX])

  const displayData = useMemo(() => {
    if (!normalised) return chartData.map(d => ({ year: d.year, wjsi: d.wjsiRaw, wjsi_with_pt: d.wjsiNopt, comp: d.compRaw }))
    const wn = normalise(chartData.map(d => d.wjsiRaw))
    const nn = normalise(chartData.map(d => d.wjsiNopt))
    const cn = normalise(chartData.map(d => d.compRaw))
    return chartData.map((d, i) => ({ year: d.year, wjsi: wn[i], wjsi_with_pt: nn[i], comp: cn[i] }))
  }, [chartData, normalised])

  const { r, n } = useMemo(() => {
    const pairs = chartData.filter(d => d.wjsiRaw != null && d.compRaw != null)
    return pairs.length < 3
      ? { r: null, n: 0 }
      : { r: pearson(pairs.map(d => d.wjsiRaw), pairs.map(d => d.compRaw)), n: pairs.length }
  }, [chartData])

  const { r: rNopt } = useMemo(() => {
    const pairs = chartData.filter(d => d.wjsiNopt != null && d.compRaw != null)
    return pairs.length < 3
      ? { r: null }
      : { r: pearson(pairs.map(d => d.wjsiNopt), pairs.map(d => d.compRaw)) }
  }, [chartData])

  const lagSweep = useMemo(() => {
    const ym = Object.fromEntries(RAW.map(d => [d.year, d]))
    return Array.from({ length: 11 }, (_, i) => i - 5).map(l => {
      const pairs = RAW.flatMap(d => {
        const raw = ym[d.year + l]?.[selectedKey] ?? null
        return raw != null ? [{ w: d.wjsi, c: invertComp ? -raw : raw }] : []
      })
      return { lag: l, r: pairs.length >= 3 ? pearson(pairs.map(p => p.w), pairs.map(p => p.c)) : null }
    })
  }, [selectedKey, invertComp])

  const bestLag = useMemo(() => {
    const v = lagSweep.filter(d => d.r != null)
    return v.length ? v.reduce((b, c) => Math.abs(c.r) > Math.abs(b.r) ? c : b) : null
  }, [lagSweep])

  return (
    <div style={{ background: '#0f0f1a', minHeight: '100vh', color: '#e0e0e0', fontFamily: 'system-ui,-apple-system,sans-serif', padding: '20px 24px', boxSizing: 'border-box' }}>
      <h1 style={{ fontSize: 18, fontWeight: 700, color: '#fff', margin: '0 0 4px' }}>Worker Job Security Index — Explorer</h1>
      <p style={{ color: '#555', fontSize: 12, margin: '0 0 20px' }}>Compare WJSI against key indicators. Lag slider shifts the comparison series to test lead/lag structure.</p>

      <div style={{ display: 'grid', gridTemplateColumns: '170px 1fr 210px', gap: 18, alignItems: 'start' }}>

        <div>
          <div style={{ color: '#444', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Compare against</div>
          {Object.entries(SERIES_META).map(([key, m]) => (
            <button key={key} onClick={() => { setSelectedKey(key); setInvertComp(m.defaultInvert) }}
              style={{
                display: 'block', width: '100%', marginBottom: 5, textAlign: 'left',
                background: selectedKey === key ? m.color + '18' : 'transparent',
                border: `1.5px solid ${selectedKey === key ? m.color : '#222'}`,
                borderRadius: 6, padding: '6px 10px', fontSize: 12,
                color: selectedKey === key ? m.color : '#555', cursor: 'pointer', transition: 'all 0.1s',
              }}>
              {m.label}
            </button>
          ))}
        </div>

        <div style={{ minWidth: 0 }}>
          <div style={{ background: '#13131e', borderRadius: 10, padding: '14px 4px 4px', marginBottom: 14 }}>
            <ResponsiveContainer width="100%" height={290}>
              <ComposedChart data={displayData} margin={{ top: 5, right: 16, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c1c2c" />
                {RECESSIONS.map(rec => (
                  <ReferenceArea key={rec.label} x1={rec.start} x2={rec.end} fill="#fff" fillOpacity={0.025}
                    label={{ value: rec.label, fill: '#333', fontSize: 9, position: 'insideTop' }} />
                ))}
                {normalised && <ReferenceLine y={50} stroke="#2a2a3a" strokeDasharray="3 3" />}
                <XAxis dataKey="year" tick={{ fill: '#444', fontSize: 11 }} tickLine={false} axisLine={{ stroke: '#222' }} />
                <YAxis tick={{ fill: '#444', fontSize: 11 }} tickLine={false} axisLine={false}
                  domain={normalised ? [0, 100] : ['auto', 'auto']} />
                <Tooltip content={<CustomTooltip compLabel={meta.label} lag={lag} inverted={invertComp} />} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#555', paddingTop: 6 }} />
                <Line type="monotone" dataKey="wjsi" name="WJSI (primary, ex pt_econ)" stroke="#4fc3f7" strokeWidth={2.5} dot={false} connectNulls />
                {showNopt && <Line type="monotone" dataKey="wjsi_with_pt" name="WJSI (with pt_econ)" stroke="#4fc3f7" strokeWidth={1.5} strokeDasharray="4 3" dot={false} strokeOpacity={0.6} connectNulls />}
                <Line type="monotone" dataKey="comp"
                  name={`${meta.label}${invertComp ? ' (inv)' : ''}${lag !== 0 ? ` [${lag > 0 ? '+' : ''}${lag}yr]` : ''}`}
                  stroke={meta.color} strokeWidth={2} dot={false}
                  strokeDasharray={lag !== 0 ? '6 3' : undefined} connectNulls />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background: '#13131e', borderRadius: 10, padding: '12px 4px 4px' }}>
            <div style={{ color: '#444', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, marginLeft: 12, marginBottom: 8 }}>
              Pearson r at each lag · positive = WJSI leads
            </div>
            <ResponsiveContainer width="100%" height={130}>
              <ComposedChart data={lagSweep} margin={{ top: 5, right: 16, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c1c2c" vertical={false} />
                <ReferenceLine y={0} stroke="#2a2a3a" />
                <ReferenceLine x={lag} stroke="#4fc3f7" strokeOpacity={0.3} />
                <XAxis dataKey="lag" tick={{ fill: '#444', fontSize: 11 }} tickLine={false} axisLine={{ stroke: '#222' }}
                  tickFormatter={v => v > 0 ? `+${v}` : String(v)} />
                <YAxis domain={[-1, 1]} tick={{ fill: '#444', fontSize: 11 }} tickLine={false} axisLine={false}
                  tickFormatter={v => v.toFixed(1)} />
                <Tooltip formatter={v => v?.toFixed(3)} labelFormatter={l => `Lag ${l > 0 ? '+' : ''}${l}yr`}
                  contentStyle={{ background: '#1a1a2e', border: '1px solid #333', borderRadius: 6, fontSize: 12 }} />
                <Line type="monotone" dataKey="r" name="r" stroke={meta.color} strokeWidth={2}
                  dot={(props) => {
                    const { cx, cy, payload } = props
                    const isBest = bestLag?.lag === payload.lag
                    const isCur = payload.lag === lag
                    return <circle key={cx} cx={cx} cy={cy} r={isBest ? 6 : isCur ? 5 : 3}
                      fill={isBest ? '#fff' : isCur ? '#4fc3f7' : meta.color}
                      stroke={meta.color} strokeWidth={1.5} />
                  }} connectNulls />
              </ComposedChart>
            </ResponsiveContainer>
            <div style={{ color: '#333', fontSize: 10, textAlign: 'center', paddingBottom: 4 }}>
              ● white = peak |r| · ● blue = current lag selection
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ background: '#13131e', borderRadius: 10, padding: '12px 14px' }}>
            <div style={{ color: meta.color, fontSize: 13, fontWeight: 600, marginBottom: 5 }}>{meta.label}</div>
            <div style={{ color: '#555', fontSize: 11, lineHeight: 1.5 }}>{meta.description}</div>
          </div>

          <div>
            <div style={{ color: '#444', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Correlation</div>
            <CorrBadge r={r} n={n} label={meta.label} lag={lag} />
            {showNopt && rNopt != null && (
              <div style={{ background: '#0c0c18', border: '1.5px solid #2a2a3a', borderRadius: 10, padding: '10px 14px', marginTop: 8 }}>
                <div style={{ fontSize: 12, color: '#555', marginBottom: 4 }}>With pt_econ</div>
                <div style={{ fontSize: 22, fontWeight: 700, color: Math.abs(rNopt) > 0.85 ? '#e74c3c' : Math.abs(rNopt) > 0.6 ? '#f39c12' : '#2ecc71', letterSpacing: -0.5 }}>
                  r = {rNopt.toFixed(3)}
                </div>
                <div style={{ fontSize: 11, color: '#555', marginTop: 4 }}>
                  Δr vs primary = {(rNopt - r).toFixed(3)} vs full index
                </div>
              </div>
            )}
            {bestLag && (
              <div style={{ color: '#555', fontSize: 11, marginTop: 8, lineHeight: 1.5 }}>
                Peak |r| = <span style={{ color: '#4fc3f7', fontWeight: 600 }}>{Math.abs(bestLag.r).toFixed(3)}</span> at{' '}
                <span style={{ color: '#4fc3f7', fontWeight: 600 }}>
                  {bestLag.lag > 0 ? `+${bestLag.lag}yr (WJSI leads)` : bestLag.lag < 0 ? `${bestLag.lag}yr (comp leads)` : 'lag 0'}
                </span>
              </div>
            )}
          </div>

          <div style={{ background: '#13131e', borderRadius: 10, padding: '12px 14px' }}>
            <div style={{ color: '#444', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Lag</div>
            <input type="range" min={-5} max={5} step={1} value={lag}
              onChange={e => setLag(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#4fc3f7', marginBottom: 4 }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#333' }}>
              <span>← comp leads</span><span>WJSI leads →</span>
            </div>
            <div style={{ textAlign: 'center', marginTop: 8, fontSize: 13, fontWeight: 600, color: lag !== 0 ? '#4fc3f7' : '#444' }}>
              {lag > 0 ? `WJSI leads ${lag}yr` : lag < 0 ? `Comp leads ${Math.abs(lag)}yr` : 'No lag'}
            </div>
          </div>

          <div style={{ background: '#13131e', borderRadius: 10, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 12, color: '#aaa' }}>
              <input type="checkbox" checked={invertComp} onChange={e => setInvertComp(e.target.checked)}
                style={{ accentColor: meta.color }} />
              Invert {meta.label}
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 12, color: '#aaa' }}>
              <input type="checkbox" checked={showNopt} onChange={e => setShowNopt(e.target.checked)}
                style={{ accentColor: '#4fc3f7' }} />
              Show WJSI with pt_econ
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 12, color: '#aaa' }}>
              <input type="checkbox" checked={normalised} onChange={e => setNormalised(e.target.checked)}
                style={{ accentColor: '#4fc3f7' }} />
              Normalise to same scale
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}
