// 할일 ↔ 구글 캘린더(10-28). 설정은 Blob cal/config.json(비공개)에 둔다
// ?f=events 구글 캘린더 일정(비공개 iCal 주소에서 읽음) · ?f=config GET 연결 상태·구독 주소, POST {ics} 구글 비공개 주소 저장
// ?f=todos POST 날짜 있는 할일 저장(구독용) · ?feed=<키> 구글 캘린더가 구독하는 할일 ics(비밀번호 대신 키)
import { put, get } from '@vercel/blob'
import { randomBytes } from 'node:crypto'

async function readJson(path, def) {
  const r = await get(path, { access: 'private', useCache: false }).catch(() => null)
  if (!r || r.statusCode !== 200) return def
  try { return JSON.parse(Buffer.from(await new Response(r.stream).arrayBuffer()).toString('utf8')) } catch { return def }
}
const save = (path, obj) => put(path, JSON.stringify(obj), { access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true })
async function config() {
  const c = await readJson('cal/config.json', {})
  if (!c.feedKey) { c.feedKey = randomBytes(18).toString('hex'); await save('cal/config.json', c) }
  return c
}
async function body(req) {
  if (req.body && typeof req.body === 'object' && !Buffer.isBuffer(req.body)) return req.body
  const chunks = []
  for await (const c of req) chunks.push(c)
  return JSON.parse(Buffer.concat(chunks).toString() || '{}')
}

// iCal 날짜 → 한국 시간 'YYYY-MM-DD' + 'HH:MM'(종일이면 빈칸)
function when(line) {
  const v = line.slice(line.lastIndexOf(':') + 1).trim()
  const m = v.match(/^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?/)
  if (!m) return null
  if (!m[4]) return { date: `${m[1]}-${m[2]}-${m[3]}`, time: '' }
  let d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]))
  if (v.endsWith('Z')) d = new Date(d.getTime() + 9 * 3600e3)   // TZID가 있으면 그 시간 그대로(한국 캘린더)
  const iso = d.toISOString()
  return { date: iso.slice(0, 10), time: iso.slice(11, 16) }
}
const unesc = (s) => s.replace(/\\n/gi, ' ').replace(/\\([,;\\])/g, '$1').trim()
function parse(ics) {
  const lines = ics.replace(/\r\n[ \t]/g, '').replace(/\n[ \t]/g, '').split(/\r?\n/)
  const out = []
  let ev = null
  for (const l of lines) {
    if (l === 'BEGIN:VEVENT') ev = {}
    else if (l === 'END:VEVENT') { if (ev?.date && ev.status !== 'CANCELLED') out.push(ev); ev = null }
    else if (ev) {
      const k = l.slice(0, l.search(/[;:]/))
      if (k === 'UID') ev.uid = l.slice(4)
      else if (k === 'SUMMARY') ev.title = unesc(l.slice(l.indexOf(':') + 1))
      else if (k === 'DTSTART') Object.assign(ev, when(l) || {})
      else if (k === 'DTEND') { const e = when(l); if (e) ev.end = e.date }
      else if (k === 'STATUS') ev.status = l.slice(7)
      else if (k === 'RRULE') ev.repeat = true
    }
  }
  return out
}

const p2 = (n) => String(n).padStart(2, '0')
const ymd = (d) => d.replace(/-/g, '')
const icsEsc = (s) => String(s).replace(/([,;\\])/g, '\\$1').replace(/\n/g, '\\n')
function feed(todos) {
  const now = new Date(), stamp = `${now.getUTCFullYear()}${p2(now.getUTCMonth() + 1)}${p2(now.getUTCDate())}T000000Z`
  const ev = todos.filter((t) => t.date).map((t) => {
    const n = new Date(t.date + 'T00:00:00Z'); n.setUTCDate(n.getUTCDate() + 1)
    return ['BEGIN:VEVENT', `UID:yujios-${t.key}@yujios`, `DTSTAMP:${stamp}`, `DTSTART;VALUE=DATE:${ymd(t.date)}`, `DTEND;VALUE=DATE:${ymd(n.toISOString().slice(0, 10))}`,
      `SUMMARY:${icsEsc((t.kind === 'start' ? '[시작] ' : '[할일] ') + t.text)}`, `DESCRIPTION:${icsEsc([t.st, t.tag, t.parent].filter(Boolean).join(' · '))}`, 'TRANSP:TRANSPARENT', 'END:VEVENT'].join('\r\n')
  })
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//yujios//todo//KO', 'CALSCALE:GREGORIAN', 'X-WR-CALNAME:유지OS 할일', 'X-WR-TIMEZONE:Asia/Seoul', ...ev, 'END:VCALENDAR', ''].join('\r\n')
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store')
  if (req.query.feed) {
    const c = await config()
    if (String(req.query.feed) !== c.feedKey) return res.status(404).send('none')
    res.setHeader('Content-Type', 'text/calendar; charset=utf-8')
    return res.status(200).send(feed(await readJson('cal/todos.json', [])))
  }
  if (!process.env.ACC_PIN || req.headers['x-pin'] !== process.env.ACC_PIN) return res.status(401).json({ error: 'pin' })
  const f = String(req.query.f || '')

  if (f === 'config') {
    const c = await config()
    if (req.method === 'POST') {
      const ics = String((await body(req)).ics || '').trim()
      if (ics && !/^https:\/\/calendar\.google\.com\/calendar\/ical\/.+\.ics$/.test(ics)) return res.status(400).json({ error: 'url' })
      c.ics = ics; await save('cal/config.json', c)
    }
    return res.status(200).json({ linked: !!c.ics, feed: `https://${req.headers.host}/api/cal?feed=${c.feedKey}` })
  }
  if (f === 'todos' && req.method === 'POST') {
    const list = (await body(req)).todos
    if (!Array.isArray(list)) return res.status(400).json({ error: 'todos' })
    await save('cal/todos.json', list.slice(0, 500))
    return res.status(200).json({ ok: true })
  }
  if (f === 'events') {
    const c = await config()
    if (!c.ics) return res.status(200).json({ linked: false, events: [] })
    const r = await fetch(c.ics).catch(() => null)
    if (!r?.ok) return res.status(200).json({ linked: true, error: '구글 캘린더를 못 읽었어요', events: [] })
    const from = new Date(Date.now() - 62 * 864e5).toISOString().slice(0, 10), to = new Date(Date.now() + 190 * 864e5).toISOString().slice(0, 10)
    const events = parse(await r.text()).filter((e) => e.date >= from && e.date <= to).sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time))
    return res.status(200).json({ linked: true, events })
  }
  return res.status(400).json({ error: 'f' })
}
