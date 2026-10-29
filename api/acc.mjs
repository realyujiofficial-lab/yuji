// 백업/불러오기: Vercel Blob(비공개). 비밀번호(ACC_PIN) 맞아야 동작
// ?f=all 전체 기록(all-data.json) · ?f=auto-<기기id> 기기별 자동 백업(auto/<id>.json) · 없으면 교통사고(accident-data.json)
// ?f=ph-<id> 할일 사진(photos/<id>.jpg, 몸통은 jpeg 바이트)
// ?f=inbox 자료 넣기 목록 · ?f=inbox-file&path=inbox/… 올리기(POST 바이트)·받기(GET)·지우기(DELETE) · ?f=inbox-done&path=… 정리됨(inbox/done/로 옮김)
// ?f=todos Claude가 넣어 둔 할일(inbox/todos.json): GET 읽기, POST 바꾸기, DELETE 비우기
import { put, get, list, del, copy } from '@vercel/blob'

const INBOX = /^inbox\/(done\/)?[^/\\]{1,200}$/

async function bodyBuf(req) {
  if (Buffer.isBuffer(req.body)) return req.body
  if (typeof req.body === 'string') return Buffer.from(req.body)
  if (req.body && typeof req.body === 'object') return Buffer.from(JSON.stringify(req.body))
  const chunks = []
  for await (const c of req) chunks.push(c)
  return Buffer.concat(chunks)
}
async function send(res, path, type) {
  const r = await get(path, { access: 'private', useCache: false })
  if (!r || r.statusCode !== 200) return res.status(404).json({ error: 'none' })
  res.setHeader('Content-Type', type || r.blob.contentType || 'application/octet-stream')
  res.status(200).send(Buffer.from(await new Response(r.stream).arrayBuffer()))
}

export default async function handler(req, res) {
  if (!process.env.ACC_PIN || req.headers['x-pin'] !== process.env.ACC_PIN) return res.status(401).json({ error: 'pin' })
  res.setHeader('Cache-Control', 'no-store')
  const f = String(req.query.f || '')

  if (/^ph-[a-z0-9]{8,40}$/.test(f)) {
    const path = `photos/${f.slice(3)}.jpg`
    if (req.method === 'POST') {
      let b = await bodyBuf(req)
      const s = b.subarray(0, 30).toString()
      if (s.startsWith('data:')) b = Buffer.from(b.toString().split(',')[1] || '', 'base64')
      await put(path, b, { access: 'private', contentType: 'image/jpeg', addRandomSuffix: false, allowOverwrite: true })
      return res.status(200).json({ ok: true })
    }
    if (req.method === 'DELETE') { await del(path).catch(() => {}); return res.status(200).json({ ok: true }) }
    return send(res, path, 'image/jpeg')
  }

  if (f === 'inbox') {
    const out = []
    let cursor
    do {
      const r = await list({ prefix: 'inbox/', cursor })
      out.push(...r.blobs.filter((b) => b.pathname !== 'inbox/todos.json').map((b) => ({ path: b.pathname, size: b.size, at: b.uploadedAt })))
      cursor = r.hasMore ? r.cursor : undefined
    } while (cursor)
    return res.status(200).json(out)
  }
  if (f === 'inbox-file' || f === 'inbox-done') {
    const path = String(req.query.path || '')
    if (!INBOX.test(path) || path.includes('..') || path === 'inbox/todos.json') return res.status(400).json({ error: 'path' })
    if (f === 'inbox-done') {
      if (path.startsWith('inbox/done/')) return res.status(200).json({ ok: true })
      const to = 'inbox/done/' + path.slice(6)
      await copy(path, to, { access: 'private', addRandomSuffix: false, allowOverwrite: true })
      await del(path)
      return res.status(200).json({ ok: true, path: to })
    }
    if (req.method === 'POST') {
      const b = await bodyBuf(req)
      await put(path, b, { access: 'private', contentType: String(req.query.type || 'application/octet-stream'), addRandomSuffix: false, allowOverwrite: true })
      return res.status(200).json({ ok: true })
    }
    if (req.method === 'DELETE') { await del(path); return res.status(200).json({ ok: true }) }
    return send(res, path)
  }
  if (f === 'todos') {
    const path = 'inbox/todos.json'
    if (req.method === 'POST') {
      await put(path, (await bodyBuf(req)).toString(), { access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true })
      return res.status(200).json({ ok: true })
    }
    if (req.method === 'DELETE') { await del(path).catch(() => {}); return res.status(200).json({ ok: true }) }
    const r = await get(path, { access: 'private', useCache: false })
    if (!r || r.statusCode !== 200) return res.status(200).json([])
    return res.status(200).send(Buffer.from(await new Response(r.stream).arrayBuffer()).toString('utf8'))
  }

  const PATH = f === 'all' ? 'all-data.json' : /^auto-[a-z0-9-]{8,40}$/.test(f) ? `auto/${f.slice(5)}.json` : f === '' ? 'accident-data.json' : null
  if (!PATH) return res.status(400).json({ error: 'f' })
  if (req.method === 'POST') {
    const body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body)
    await put(PATH, body, { access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true })
    return res.status(200).json({ ok: true })
  }
  const r = await get(PATH, { access: 'private', useCache: false })
  if (!r) return res.status(404).json({ error: 'none' })
  res.status(200).send(Buffer.from(await new Response(r.stream).arrayBuffer()).toString('utf8'))
}
