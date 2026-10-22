// 오픈카톡방 제보(upload.html): Vercel Blob(비공개) reports/… 저장. 제보 올리기는 누구나, 목록·읽기·승인·삭제는 비밀번호(ACC_PIN)
import { put, get, list, del } from '@vercel/blob'

const OK_PATH = /^reports\/(pending|approved\/[^/]{1,30})\/\d{10,16}\.json$/

export default async function handler(req, res) {
  const path = req.query.path || ''
  const admin = !!process.env.ACC_PIN && req.headers['x-pin'] === process.env.ACC_PIN
  const publicSubmit = req.method === 'POST' && /^reports\/pending\/\d{10,16}\.json$/.test(path)
  if (!admin && !publicSubmit) return res.status(401).json({ error: 'pin' })
  res.setHeader('Cache-Control', 'no-store')

  if (req.method === 'GET' && req.query.list) {
    const { blobs } = await list({ prefix: req.query.list })
    return res.status(200).json(blobs.map((b) => ({ name: b.pathname.slice(req.query.list.length) })))
  }
  if (req.method === 'GET' && !path) return res.status(200).json({ ok: true })
  if (!OK_PATH.test(path)) return res.status(400).json({ error: 'path' })

  if (req.method === 'POST') {
    const body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body)
    if (body.length > 20000) return res.status(413).json({ error: 'big' })
    await put(path, body, { access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true })
    return res.status(200).json({ ok: true })
  }
  if (req.method === 'DELETE') {
    const { blobs } = await list({ prefix: path })
    if (blobs.length) await del(blobs.map((b) => b.url))
    return res.status(200).json({ ok: true })
  }
  const r = await get(path, { access: 'private', useCache: false })
  if (!r) return res.status(404).json({ error: 'none' })
  res.status(200).send(Buffer.from(await new Response(r.stream).arrayBuffer()).toString('utf8'))
}
