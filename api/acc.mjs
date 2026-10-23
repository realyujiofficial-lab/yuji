// 백업/불러오기: Vercel Blob(비공개). ?f=all이면 전체 기록(all-data.json), ?f=auto-<기기id>면 기기별 자동 백업(auto/<id>.json), 아니면 교통사고(accident-data.json). 비밀번호(ACC_PIN) 맞아야 동작
import { put, get } from '@vercel/blob'

export default async function handler(req, res) {
  if (!process.env.ACC_PIN || req.headers['x-pin'] !== process.env.ACC_PIN) return res.status(401).json({ error: 'pin' })
  const f = String(req.query.f || '')
  const PATH = f === 'all' ? 'all-data.json' : /^auto-[a-z0-9-]{8,40}$/.test(f) ? `auto/${f.slice(5)}.json` : 'accident-data.json'
  if (req.method === 'POST') {
    const body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body)
    await put(PATH, body, { access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true })
    return res.status(200).json({ ok: true })
  }
  const r = await get(PATH, { access: 'private', useCache: false })
  if (!r) return res.status(404).json({ error: 'none' })
  res.setHeader('Cache-Control', 'no-store')
  res.status(200).send(Buffer.from(await new Response(r.stream).arrayBuffer()).toString('utf8'))
}
