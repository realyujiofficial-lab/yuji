#!/usr/bin/env python3
"""오카방 대화 통계 추출 — 정제본 파일 → _workspace/stats.json"""
import re, json, os
from collections import defaultdict
from datetime import datetime, timedelta

BASE_DIR = "/mnt/c/Users/ryu53/Downloads/깃허브/harness-main/놀생_오픈카톡방"
PROCESSED_DIR = os.path.join(BASE_DIR, "대화기록", "정제본")
WORKSPACE = os.path.join(BASE_DIR, "_workspace")
OUTPUT = os.path.join(WORKSPACE, "stats.json")
os.makedirs(WORKSPACE, exist_ok=True)

DATE_RE = re.compile(r'^--- (\d{4}년 \d+월 \d+일) ---')
MSG_RE  = re.compile(r'^\[(\d{2}:\d{2})\] (.+?): (.+)$')
SKIP    = {"사진", "이모티콘", "동영상", "파일", "연락처", "지도", "투표"}

def date_key(d):
    m = re.match(r'(\d{4})년 (\d+)월 (\d+)일', d)
    return (int(m[1]), int(m[2]), int(m[3])) if m else (0, 0, 0)

def parse_file(fp):
    msgs = []
    cur = None
    try:
        with open(fp, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip()
                dm = DATE_RE.match(line)
                if dm:
                    cur = dm.group(1); continue
                mm = MSG_RE.match(line)
                if mm and cur:
                    nick, text = mm.group(2), mm.group(3)
                    if nick == "오픈채팅봇": continue
                    msgs.append({"date": cur, "time": mm.group(1), "nick": nick, "text": text})
    except Exception as e:
        print(f"  [WARN] {fp}: {e}")
    return msgs

# 정보방 파일만 로드 (수다방 제외)
all_msgs = []
for fname in sorted(os.listdir(PROCESSED_DIR)):
    if fname.endswith(".txt") and "수다방" not in fname:
        all_msgs.extend(parse_file(os.path.join(PROCESSED_DIR, fname)))

# 날짜별 집계
daily = defaultdict(lambda: {"msgs": 0, "users": set(), "texts": []})
for msg in all_msgs:
    d = msg["date"]
    daily[d]["msgs"] += 1
    daily[d]["users"].add(msg["nick"])
    txt = msg["text"].strip()
    if txt not in SKIP and not txt.startswith("http") and len(txt) > 2:
        daily[d]["texts"].append(f"{msg['nick']}: {txt[:60]}")

# 유저별 마지막 활동일 + 메시지 수
user_last = defaultdict(lambda: {"msgs": 0, "last": None})
for msg in all_msgs:
    n = msg["nick"]
    user_last[n]["msgs"] += 1
    if user_last[n]["last"] is None or date_key(msg["date"]) > date_key(user_last[n]["last"]):
        user_last[n]["last"] = msg["date"]

# 정렬된 날짜 목록 (최근 90일)
all_dates = sorted(daily.keys(), key=date_key)[-90:]

# 오늘 기준 계산
now = datetime.now()
today_key = (now.year, now.month, now.day)

def days_ago(date_str, ref=today_key):
    k = date_key(date_str)
    d1 = datetime(*ref)
    d2 = datetime(*k)
    return (d1 - d2).days

# 비활동 멤버: 현재 활성 유저 중 30일+ 침묵
# 최근 30일 활성 유저 (메시지 있는)
recent_active = {msg["nick"] for msg in all_msgs if days_ago(msg["date"]) <= 30}
# 30일 이전 활동, 이후 없음 = 이탈 위험
at_risk = {
    nick: info for nick, info in user_last.items()
    if nick not in recent_active
    and info["msgs"] >= 10
    and days_ago(info["last"]) <= 90
}

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "all_dates": all_dates,
    "daily": {
        d: {
            "msgs": daily[d]["msgs"],
            "users": len(daily[d]["users"]),
            "user_list": sorted(daily[d]["users"]),
            "sample_texts": daily[d]["texts"][:15]
        }
        for d in all_dates
    },
    "user_stats": dict(
        sorted(user_last.items(), key=lambda x: -x[1]["msgs"])[:80]
    ),
    "at_risk": {
        nick: {"msgs": v["msgs"], "last": v["last"], "days_silent": days_ago(v["last"])}
        for nick, v in sorted(at_risk.items(), key=lambda x: x[1]["msgs"], reverse=True)[:20]
    },
    "recent_7d_avg": round(
        sum(daily[d]["msgs"] for d in all_dates if days_ago(d) <= 7) / 7, 1
    ) if all_dates else 0,
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

last = all_dates[-1] if all_dates else "N/A"
print(f"✅ stats.json 생성 완료")
print(f"   기간: {all_dates[0] if all_dates else 'N/A'} ~ {last}")
print(f"   최근 7일 일평균: {result['recent_7d_avg']}개")
print(f"   이탈 위험 멤버: {len(result['at_risk'])}명")
