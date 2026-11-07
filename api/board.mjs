// 8주 만다라트 같이 쓰기(/mandalart.html) 저장 API — 놀생 Supabase(nollife-stats) 표 mandal_board
// 11-07 Vercel Blob을 2초마다 읽다가 무료 한도 초과로 정지 → Supabase로 옮김(읽기 횟수 한도 없음).
// GET ?k=&v=1 → {rev}(바뀐 번호만, 아주 작음) · GET ?k= → {A,B,X,rev} · POST ?k=&w=A|B|X 몸통=바뀐 칸만 → 서버에서 합침
// 합치기는 DB 함수 mandal_patch가 한 번에 처리(읽고-덮어쓰기 없음), 바뀌기 전 내용은 mandal_history에 5분마다 남김.
const URL_ = (process.env.NOLLIFE_SB_URL || '').trim().replace(/\/rest\/v1\/?$/, '').replace(/\/$/, '')
const KEY = process.env.NOLLIFE_SB_SERVICE_KEY
const K = /^[a-z0-9]{10,40}$/
const W = ['A', 'B', 'X']

async function sb(path, opt = {}) {
  const r = await fetch(`${URL_}/rest/v1/${path}`, {
    ...opt,
    headers: { apikey: KEY, Authorization: `Bearer ${KEY}`, 'Content-Type': 'application/json', ...(opt.headers || {}) },
  })
  if (!r.ok) throw new Error(`sb ${r.status} ${(await r.text()).slice(0, 120)}`)
  return r.json()
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store')
  try { return await main(req, res) } catch (e) { return res.status(503).json({ error: 'store', detail: String(e && e.message || e).slice(0, 160) }) }
}

async function main(req, res) {
  if (!URL_ || !KEY) throw new Error('env')
  const k = String(req.query.k || '')
  if (!K.test(k)) return res.status(400).json({ error: 'key' })
  if (req.method === 'POST') {
    const w = String(req.query.w || '')
    if (!W.includes(w)) return res.status(400).json({ error: 'who' })
    let patch = req.body
    if (typeof patch === 'string') { try { patch = JSON.parse(patch) } catch { patch = null } }
    if (!patch || typeof patch !== 'object' || Array.isArray(patch)) return res.status(400).json({ error: 'body' })
    const clean = {}
    for (const [key, v] of Object.entries(patch)) {
      if (!/^[A-Za-z0-9_]{1,20}$/.test(key)) continue
      if (v === null) clean[key] = null
      else if (['string', 'number', 'boolean'].includes(typeof v)) clean[key] = typeof v === 'string' ? v.slice(0, 500) : v
    }
    const out = await sb('rpc/mandal_patch', { method: 'POST', body: JSON.stringify({ p_k: k, p_w: w, p_patch: clean }) })
    return res.status(200).json(out)
  }
  const rows = await sb(`mandal_board?k=eq.${k}&select=w,rev${req.query.v ? '' : ',data'}`)
  const rev = rows.reduce((n, r) => n + Number(r.rev || 0), 0)
  if (req.query.v) return res.status(200).json({ rev })
  const out = { A: {}, B: {}, X: {}, rev }
  for (const r of rows) if (W.includes(r.w)) out[r.w] = r.data || {}
  return res.status(200).json(out)
}
