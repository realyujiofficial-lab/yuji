// 8주 만다라트 같이 쓰기(/mandalart.html): 로그인 없이 링크 키(k)로 구분, Vercel Blob(비공개) board/<k>/<A|B|X>.json
// GET ?k= → {A,B,X} · POST ?k=&w=A|B|X 몸통 = 바뀐 칸만(JSON) → 합쳐서 저장
import { put, get } from '@vercel/blob'

const KEY = /^[a-z0-9]{10,40}$/
const W = ['A', 'B', 'X']

// 읽기 실패를 빈 칸({})으로 처리하면 저장할 때 원래 내용을 덮어쓴다(11-07 사고). 없는 파일만 {}, 나머지 실패는 오류로.
async function read(k, w) {
  let r
  try { r = await get(`board/${k}/${w}.json`, { access: 'private', useCache: false }) }
  catch (e) { if (/not.?found|404/i.test(String(e && (e.message || e)))) return {}; throw e }
  if (!r) return {}
  if (r.statusCode !== 200) throw new Error('blob ' + r.statusCode)
  return JSON.parse(Buffer.from(await new Response(r.stream).arrayBuffer()).toString('utf8'))
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store')
  try { return await main(req, res) } catch (e) { return res.status(503).json({ error: 'store', detail: String(e && e.message || e).slice(0, 120) }) }
}
async function main(req, res) {
  const k = String(req.query.k || '')
  if (!KEY.test(k)) return res.status(400).json({ error: 'key' })
  if (req.method === 'POST') {
    const w = String(req.query.w || '')
    if (!W.includes(w)) return res.status(400).json({ error: 'who' })
    let patch = req.body
    if (typeof patch === 'string') { try { patch = JSON.parse(patch) } catch { patch = null } }
    if (!patch || typeof patch !== 'object' || Array.isArray(patch)) return res.status(400).json({ error: 'body' })
    const cur = await read(k, w)
    for (const [key, v] of Object.entries(patch)) {
      if (!/^[A-Za-z0-9_]{1,20}$/.test(key)) continue
      if (v === null) delete cur[key]
      else if (['string', 'number', 'boolean'].includes(typeof v)) cur[key] = typeof v === 'string' ? v.slice(0, 500) : v
    }
    const body = JSON.stringify(cur)
    if (body.length > 100000) return res.status(413).json({ error: 'big' })
    await put(`board/${k}/${w}.json`, body, { access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true })
    return res.status(200).json(cur)
  }
  const [A, B, X] = await Promise.all(W.map((w) => read(k, w)))
  return res.status(200).json({ A, B, X })
}
