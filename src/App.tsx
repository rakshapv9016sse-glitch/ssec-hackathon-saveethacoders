import { useEffect, useMemo, useState } from 'react'

type Purpose = 'Coloring worksheet' | 'Educational flashcard' | 'Classroom poster' | 'Official publication'
type Item = { id: string; prompt: string; purpose: Purpose; time: string; mode: string; preview_url: string; download_url: string }
type Generation = { id: string; prompt: string; purpose: string; detected_concept: string; selected_pipeline: string; elapsed_ms: number; width: number; height: number; actual_dimensions: { width: number; height: number }; output_size_bytes: number; download_url: string; preview_url: string; reason: string; quality_checks: Record<string, boolean | null | string[]>; created_at: string }
type Metrics = { successful_generations: number; worksheet_images: number; flashcards: number; posters: number; total_processing_ms: number; total_output_size_bytes: number; fallback_count: number; pipeline_usage: { purpose: string; count: number }[]; benchmark_records: number }

const API_BASE = 'http://127.0.0.1:8000'
const PURPOSE_IDS: Record<Purpose, string> = {
  'Coloring worksheet': 'coloring_worksheet',
  'Educational flashcard': 'educational_flashcard',
  'Classroom poster': 'classroom_poster',
  'Official publication': 'official_publication'
}

const purposes: { name: Purpose; icon: string; desc: string; mode: string; color: string }[] = [
  { name: 'Coloring worksheet', icon: '✎', desc: 'Clean black outlines for printing', mode: 'B&W outline', color: 'mint' },
  { name: 'Educational flashcard', icon: '▣', desc: 'Bright, simple learning visuals', mode: 'Simple color', color: 'blue' },
  { name: 'Classroom poster', icon: '▧', desc: 'Engaging visuals for a classroom', mode: 'Rich color', color: 'purple' },
  { name: 'Official publication', icon: '✦', desc: 'Polished output for public use', mode: 'High quality', color: 'orange' }
]

function ElephantPreview({ purpose }: { purpose: Purpose }) {
  const outline = purpose === 'Coloring worksheet'
  const bg = outline ? '#ffffff' : purpose === 'Educational flashcard' ? '#e9f8f1' : purpose === 'Classroom poster' ? '#f1eaff' : '#fff4e6'
  const fill = outline ? '#ffffff' : purpose === 'Educational flashcard' ? '#79cdb5' : purpose === 'Classroom poster' ? '#b7a2f4' : '#8bb6d9'
  const stroke = outline ? '#171717' : '#35465a'
  return <svg className="elephant" viewBox="0 0 360 270" role="img" aria-label="Example elephant illustration">
    <rect x="0" y="0" width="360" height="270" rx="18" fill={bg}/>
    {!outline && <><circle cx="46" cy="38" r="17" fill="#ffd76a"/><path d="M0 220 Q90 188 180 220 T360 220 V270 H0Z" fill={purpose === 'Educational flashcard' ? '#d3f0df' : '#e1d7fb'}/></>}
    <g stroke={stroke} strokeWidth={outline ? 3 : 2.5} strokeLinejoin="round" strokeLinecap="round">
      <ellipse cx="166" cy="153" rx="74" ry="53" fill={fill}/>
      <ellipse cx="124" cy="119" rx="37" ry="43" fill={fill}/>
      <circle cx="200" cy="110" r="48" fill={fill}/>
      <ellipse cx="174" cy="117" rx="28" ry="34" fill={outline ? '#fff' : '#cce8e1'}/>
      <path d="M228 121 C249 141 245 177 224 188 C211 194 204 185 211 174 C224 158 213 143 213 140" fill={fill}/>
      <path d="M119 196 L119 221 Q119 228 129 228 H144 Q151 228 151 220 L151 199" fill={fill}/>
      <path d="M181 199 L181 220 Q181 228 190 228 H206 Q213 228 211 219 L208 191" fill={fill}/>
      <path d="M91 150 Q75 165 87 181" fill="none"/>
      <circle cx="213" cy="101" r="4.5" fill={stroke} stroke="none"/>
      <path d="M236 142 Q245 148 239 157" fill="none"/>
    </g>
    {purpose !== 'Coloring worksheet' && <g fill="#536477" fontSize="11" fontWeight="700"><text x="22" y="245">LEARN • EXPLORE • DISCOVER</text></g>}
    {purpose === 'Coloring worksheet' && <text x="180" y="250" textAnchor="middle" fill="#222" fontSize="12" fontWeight="700">COLOUR THE ELEPHANT</text>}
  </svg>
}

export default function App() {
  const [prompt, setPrompt] = useState('Create a friendly elephant for Grade 2 students')
  const [purpose, setPurpose] = useState<Purpose>('Coloring worksheet')
  const [grade, setGrade] = useState('Grade 2')
  const [complexity, setComplexity] = useState('Simple')
  const [format, setFormat] = useState('Portrait 4:5')
  const [quality, setQuality] = useState('Standard')
  const [generating, setGenerating] = useState(false)
  const [benchmarking, setBenchmarking] = useState(false)
  const [apiConnected, setApiConnected] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<Generation | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [benchmarkResults, setBenchmarkResults] = useState<Record<string, unknown>[]>([])
  const [generated, setGenerated] = useState(false)
  const [tab, setTab] = useState('Create')
  const [history, setHistory] = useState<Item[]>([])
  const selected = purposes.find(p => p.name === purpose)!
  const estimate = useMemo(() => purpose === 'Coloring worksheet' ? 'svg_line_art' : purpose === 'Educational flashcard' ? 'svg_educational_illustration' : 'layered_svg_poster', [purpose])

  async function refreshData() {
    try {
      const [historyResponse, metricsResponse, healthResponse] = await Promise.all([
        fetch(`${API_BASE}/api/history`), fetch(`${API_BASE}/api/metrics`), fetch(`${API_BASE}/api/health`)
      ])
      if (!historyResponse.ok || !metricsResponse.ok || !healthResponse.ok) throw new Error('Local API unavailable')
      const records = await historyResponse.json()
      setHistory(records.map((record: Generation) => ({
        id: record.id,
        prompt: record.prompt,
        purpose: purposes.find(option => PURPOSE_IDS[option.name] === record.purpose)?.name ?? 'Classroom poster',
        time: new Date((record as Generation & { created_at: string }).created_at).toLocaleString(),
        mode: record.selected_pipeline.replaceAll('_', ' '),
        preview_url: record.preview_url,
        download_url: record.download_url
      })))
      setMetrics(await metricsResponse.json())
      setApiConnected(true)
    } catch {
      setApiConnected(false)
    }
  }

  useEffect(() => { void refreshData() }, [])

  async function generate() {
    if (!prompt.trim()) return
    setGenerating(true)
    setError('')
    try {
      const sizes: Record<string, [number, number]> = {
        'Portrait 4:5': [800, 1000], 'Square 1:1': [1000, 1000],
        'Landscape 16:9': [1200, 675], 'A4 Print': [800, 1131]
      }
      const [width, height] = sizes[format]
      const complexityValue = complexity === 'Very simple' || complexity === 'Simple' ? 'simple' : complexity === 'Balanced' ? 'moderate' : 'detailed'
      const response = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt, purpose: PURPOSE_IDS[purpose], grade_group: grade, complexity: complexityValue,
          color_requirement: purpose === 'Coloring worksheet' ? 'black_white' : 'color',
          width, height, usage: format === 'A4 Print' ? 'print' : 'screen',
          quality_preference: quality === 'High quality' ? 'high' : 'standard'
        })
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Image generation failed.')
      setResult(data)
      setGenerated(true)
      setApiConnected(true)
      await refreshData()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not generate the image. Check the local backend.')
    } finally {
      setGenerating(false)
    }
  }

  async function runBenchmark() {
    setBenchmarking(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE}/api/benchmark`, { method: 'POST' })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Benchmark failed.')
      setBenchmarkResults(data.results)
      await refreshData()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not run the benchmark.')
    } finally {
      setBenchmarking(false)
    }
  }

  function downloadPreview() {
    const svg = document.querySelector('.elephant') as SVGSVGElement | null
    if (!svg) return
    const blob = new Blob([new XMLSerializer().serializeToString(svg)], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'smartgen-preview.svg'
    a.click()
    URL.revokeObjectURL(url)
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">✦</div><div><strong>SmartGen<span> AI</span></strong><small>Purpose-aware generation</small></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav>
        {['Create', 'Generation history', 'Resource analytics', 'Comparison lab'].map((item, i) =>
          <button key={item} className={`nav-item ${tab === item ? 'active' : ''}`} onClick={() => setTab(item)}>
            <span className="nav-icon">{['✧', '◷', '▥', '⇄'][i]}</span>{item}
            {item === 'Create' && <span className="nav-dot"/>}
          </button>
        )}
      </nav>
      <div className="sidebar-bottom">
        <div className="status-card"><span className="status-dot"/> <div><b>{apiConnected ? 'Local engine online' : 'Local engine offline'}</b><small>{metrics ? `${metrics.successful_generations} saved generations` : 'Waiting for backend'}</small></div></div>
        <div className="profile"><div className="avatar">SG</div><div><b>SmartGen Team</b><small>HackFest '26 · PS 1</small></div><span className="dots">···</span></div>
      </div>
    </aside>

    <main className="main">
      <header className="topbar">
        <div className="crumb">Workspace <span>/</span> <b>{tab}</b></div>
        <div className="top-actions"><span className="demo-pill"><i/>{apiConnected ? 'Local API connected' : 'Backend offline'}</span><button className="help-btn" onClick={() => void refreshData()}>↻ <span>Refresh</span></button></div>
      </header>
      {error && <div className="strategy-box" role="alert"><div className="strategy-icon">!</div><div><b>Request failed</b><p>{error}</p></div></div>}

      {tab === 'Create' ? <div className="page-content">
        <section className="welcome-row">
          <div><div className="eyebrow"><span className="spark">✦</span> SMARTER IMAGE GENERATION</div><h1>Ask the purpose.<br/><em>Then generate.</em></h1><p>Every image has a job to do. SmartGen chooses a fit-for-purpose generation approach to reduce wasted compute without compromising what matters.</p></div>
          <div className="welcome-art"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="art-core">✦</div><div className="floating-card card-a">◉ <span>Purpose</span></div><div className="floating-card card-b">ϟ <span>Resources</span></div><div className="floating-card card-c">✓ <span>Quality</span></div></div>
        </section>

        <div className="section-heading"><div><span className="step-number">01</span><div><h2>What are you creating?</h2><p>Choose the intended use. We’ll adapt the generation strategy.</p></div></div><span className="required">Required <b>*</b></span></div>
        <div className="purpose-grid">
          {purposes.map(p => <button key={p.name} onClick={() => { setPurpose(p.name); setGenerated(false); setResult(null) }} className={`purpose-card ${purpose === p.name ? 'chosen' : ''}`}>
            <div className={`purpose-icon ${p.color}`}>{p.icon}</div><div className="purpose-copy"><b>{p.name}</b><span>{p.desc}</span></div><span className={`radio ${purpose === p.name ? 'checked' : ''}`}>{purpose === p.name ? '✓' : ''}</span>
          </button>)}
        </div>

        <div className="builder-grid">
          <section className="panel prompt-panel">
            <div className="panel-title"><div><span className="step-number">02</span><div><h2>Describe your image</h2><p>Be clear about the subject and audience.</p></div></div><span className="optional">Optional details below</span></div>
            <label className="field-label" htmlFor="prompt">IMAGE PROMPT</label>
            <textarea id="prompt" value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Describe the image you want to create..." rows={4}/>
            <div className="prompt-footer"><span>✧ Try: “A butterfly life cycle for Grade 3”</span><span>{prompt.length}/500</span></div>
            <div className="fields-row">
              <div className="field"><label className="field-label">TARGET AUDIENCE</label><select value={grade} onChange={e => setGrade(e.target.value)}><option>Pre-K</option><option>Grade 1</option><option>Grade 2</option><option>Grade 3</option><option>Grade 4–5</option><option>General audience</option></select></div>
              <div className="field"><label className="field-label">VISUAL COMPLEXITY</label><select value={complexity} onChange={e => setComplexity(e.target.value)}><option>Very simple</option><option>Simple</option><option>Balanced</option><option>Detailed</option></select></div>
            </div>
            <div className="fields-row">
              <div className="field"><label className="field-label">OUTPUT FORMAT</label><select value={format} onChange={e => setFormat(e.target.value)}><option>Portrait 4:5</option><option>Square 1:1</option><option>Landscape 16:9</option><option>A4 Print</option></select></div>
              <div className="field"><label className="field-label">QUALITY TARGET</label><select value={quality} onChange={e => setQuality(e.target.value)}><option>Draft</option><option>Standard</option><option>High quality</option></select></div>
            </div>
            <div className="strategy-box"><div className="strategy-icon">✦</div><div><b>Recommended strategy <span>SMART PICK</span></b><p>{purpose === 'Coloring worksheet' ? 'Monochrome outline · minimal detail · print-friendly background' : purpose === 'Educational flashcard' ? 'Simple color palette · clear subject · classroom-card layout' : purpose === 'Classroom poster' ? 'Rich color palette · balanced composition · poster layout' : 'High-detail treatment · publication-ready composition'}</p></div></div>
            <button className="generate-btn" onClick={generate} disabled={generating || !prompt.trim()}>{generating ? <><span className="spinner"/> Generating PNG...</> : <>✦ Generate image <span>→</span></>}</button>
            {error && <p role="alert" className="privacy-note">{error}</p>}
            <div className="privacy-note">⌁ Local PNG generation · No external API calls</div>
          </section>

          <section className="panel preview-panel">
            <div className="preview-head"><div><h2>Live preview</h2><p>Your purpose-aware result</p></div><span className="preview-status"><i/>{generated ? 'Preview ready' : 'Ready to preview'}</span></div>
            <div className="preview-canvas"><div className="canvas-badge">{result?.selected_pipeline.replaceAll('_', ' ') ?? selected.mode}</div>{result ? <img className="elephant" src={`${API_BASE}${result.preview_url}`} alt={`Generated ${result.detected_concept} for ${purpose}`}/> : <ElephantPreview purpose={purpose}/>}<div className="preview-caption"><span className="mini-spark">✦</span><b>{result ? `${result.actual_dimensions.width} × ${result.actual_dimensions.height}px · ${(result.output_size_bytes / 1024).toFixed(1)} KB` : 'Your canvas is ready'}</b><small>{result ? `${result.elapsed_ms.toFixed(2)} ms · objective checks passed` : 'Choose a purpose and generate a preview'}</small></div></div>
            <div className="preview-meta"><div><span>PURPOSE</span><b>{purpose}</b></div><div><span>FORMAT</span><b>{format}</b></div><div><span>QUALITY</span><b>{quality}</b></div></div>
            {result && <div className="preview-meta">{Object.entries(result.quality_checks).filter(([key, value]) => key !== 'passed' && key !== 'notes' && typeof value === 'boolean').map(([check, passed]) => <div key={check}><span>{check.replaceAll('_', ' ')}</span><b>{passed ? 'Pass' : 'Review'}</b></div>)}</div>}
            {result ? <a className="download-btn" href={`${API_BASE}${result.download_url}`} download>↓ Download generated image <span>PNG</span></a> : <button className="download-btn" onClick={downloadPreview}>↓ Download example <span>SVG</span></button>}
            <div className="resource-card"><div className="resource-head"><span>ϟ</span><div><b>Selected local pipeline</b><small>{result?.reason ?? 'Purpose-aware local rendering'}</small></div></div><div className="resource-metrics"><div><span>Pipeline</span><b>{result?.selected_pipeline ?? estimate}</b></div><div><span>Measured runtime</span><b>{result ? `${result.elapsed_ms.toFixed(2)} ms` : 'Not run'}</b></div></div><small className="estimate-note">Procedural vector templates, rendered locally. No model inference or estimated cloud savings.</small></div>
          </section>
        </div>

        <section className="bottom-row"><div className="bottom-title"><div><span className="step-number">03</span><div><h2>Recent generations</h2><p>Pick up where you left off.</p></div></div><button onClick={() => setTab('Generation history')} className="text-btn">View all →</button></div>
          <div className="history-list">{history.slice(0, 3).map(item => <div className="history-item" key={item.id}><img className="history-thumb" src={`${API_BASE}${item.preview_url}`} alt=""/><div className="history-copy"><b>{item.prompt}</b><span>{item.purpose} · {item.mode}</span></div><span className="history-time">{item.time}</span><a className="more-btn" href={`${API_BASE}${item.download_url}`} download aria-label="Download generated image">↓</a></div>)}</div>
        </section>
        <footer><span>✦ SmartGen AI</span><span>Ask the purpose, then generate. <b>·</b> Sakthi HackFest '26</span></footer>
      </div> : <div className="page-content secondary-page">
        <div className="eyebrow"><span className="spark">✦</span> SMARTGEN AI WORKSPACE</div><h1>{tab}</h1><p className="secondary-intro">{tab === 'Generation history' ? 'Review your recent image requests and their selected generation strategies.' : tab === 'Resource analytics' ? 'Understand how purpose-aware generation can allocate compute more efficiently.' : 'Compare how the same prompt can be handled differently for different purposes.'}</p>
        {tab === 'Generation history' ? <div className="panel history-full">{history.map(item => <div className="history-item" key={item.id}><img className="history-thumb" src={`${API_BASE}${item.preview_url}`} alt=""/><div className="history-copy"><b>{item.prompt}</b><span>{item.purpose} · {item.mode}</span></div><span className="history-time">{item.time}</span><a className="more-btn" href={`${API_BASE}${item.download_url}`} download aria-label="Download generated image">↓</a></div>)}</div> :
        tab === 'Resource analytics' ? <div className="analytics-grid"><div className="panel analytic"><span>SAVED GENERATIONS</span><b>{metrics?.successful_generations ?? 0}</b><small>Persistent local records</small></div><div className="panel analytic"><span>FALLBACKS USED</span><b>{metrics?.fallback_count ?? 0}</b><small>Tracked local render fallbacks</small></div><div className="panel analytic"><span>OUTPUT STORAGE</span><b>{metrics ? `${(metrics.total_output_size_bytes / 1024).toFixed(1)} KB` : '0 KB'}</b><small>Actual PNG bytes</small></div><div className="panel analytic wide"><h2>Saved generations by purpose</h2>{purposes.map(p => { const count = metrics?.pipeline_usage.find(item => item.purpose === PURPOSE_IDS[p.name])?.count ?? 0; const maximum = Math.max(1, ...(metrics?.pipeline_usage.map(item => item.count) ?? [0])); return <div className="bar-row" key={p.name}><span>{p.name}</span><div className="bar"><i style={{width: `${count / maximum * 100}%`}}/></div><b>{count}</b></div> })}</div></div> :
        <><div className="section-heading"><div><span className="step-number">01</span><div><h2>Local measured benchmark</h2><p>Ten fixed prompts; output dimensions and measurements are reported separately.</p></div></div><button className="generate-btn" onClick={runBenchmark} disabled={benchmarking}>{benchmarking ? 'Running benchmark...' : 'Run 10-case benchmark'}</button></div>{benchmarkResults.length > 0 && <div className="history-list">{benchmarkResults.map((item, index) => <div className="history-item" key={String(item.test_case_id ?? index)}><div className="history-thumb">{item.optimized_quality_status ? '✓' : '!'}</div><div className="history-copy"><b>{String(item.prompt)}</b><span>{String(item.optimized_pipeline).replaceAll('_', ' ')}</span></div><span className="history-time">{item.optimized_elapsed_ms == null ? 'Failed' : `${Number(item.optimized_elapsed_ms).toFixed(2)} ms · ${Number(item.optimized_size_bytes).toLocaleString()} B`}</span></div>)}</div>}<div className="compare-grid">{purposes.map(p => <div className="panel compare-card" key={p.name}><div className={`purpose-icon ${p.color}`}>{p.icon}</div><h2>{p.name}</h2><p>{p.desc}</p><div className="compare-stat"><span>Local pipeline</span><b>{p.mode}</b></div><button className="download-btn" onClick={() => {setPurpose(p.name);setTab('Create')}}>Create for this purpose →</button></div>)}</div></>}
        <button className="back-btn" onClick={() => setTab('Create')}>← Back to image creator</button>
        <footer><span>✦ SmartGen AI</span><span>Local API · SQLite-backed records</span></footer>
      </div>}
    </main>
  </div>
}
