#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카카오톡 오픈채팅방 유저 추적 Excel 생성 (정보방 전용)
"""

import re, os
from collections import defaultdict
from datetime import datetime, timedelta
import pandas as pd

BASE_DIR = "/mnt/c/Users/ryu53/Downloads/깃허브/harness-main/놀생_오픈카톡방"
INPUT_DIR  = os.path.join(BASE_DIR, "대화기록", "원본")
DATA_DIR   = os.path.join(BASE_DIR, "데이터")
OUTPUT_XLSX   = os.path.join(DATA_DIR, "유저_추적.xlsx")
OUTPUT_REPORT = os.path.join(DATA_DIR, "운영_리포트.xlsx")
OUTPUT_NICKMAP = os.path.join(DATA_DIR, "닉네임_매핑.xlsx")

# ─────────────────────────────────────────────────────────────
# 닉네임 매핑 (구형 → 현재)
# 검증 기준: 동일 시간/메시지 비교 or 동일 닉네임 키워드 유지
# ─────────────────────────────────────────────────────────────
NICK_MAP = {
    # ── 메시지 비교로 직접 확인된 매핑 ──
    "인천/woo":                         "서울/응원하는 라이언",   # 2024-01-06 동일메시지 확인
    "당진&여수/뭉이도사":                "충남당진&전남여수/전국구맛집/뭉이",
    "충남/당진&전남/여수/뭉이":          "충남당진&전남여수/전국구맛집/뭉이",
    "당진/뭉이도사":                     "충남당진&전남여수/전국구맛집/뭉이",
    "군산&서울 송파,광진/닭국밥":        "전북 군산&서울 송파/로컬여행/닭국밥",
    "군산&서울/닭국밥":                  "전북 군산&서울 송파/로컬여행/닭국밥",
    "서울 성동구/ 먹기위해일한다":       "경기 고양 일산동구/로컬맛집/먹위일",
    "서울성동구/먹기위해일한다":         "경기 고양 일산동구/로컬맛집/먹위일",
    "서울/먹기위해일한다":               "경기 고양 일산동구/로컬맛집/먹위일",
    "인천 부평/딸기":                    "리본/인천",
    "인천/딸기":                         "리본/인천",
    "서울/냠냠":                         "서울 강남구/냠냠",
    "경기양주 봉기":                     "경기양주/ 봉기",
    "양주 봉기":                         "경기양주/ 봉기",
    "양주/봉기":                         "경기양주/ 봉기",
    "미국 / 옴팡":                       "해외미국/옴팡",
    "미국/옴팡":                         "해외미국/옴팡",
    "제주/소멍태":                       "제주도 제주시/올레길, 맛집/소멍태",
    "전주/무한":                         "전북 전주시 완산구/사진&맛집/ 무한",
    "서울/루팡":                         "서울 강동구/루팡",
    # ── 닉네임 키워드 동일, 지역정보 확장된 경우 (고신뢰) ──
    "부산 / 어피치":                     "부산 / 수영구 / 맛집 / 어피치",
    "부산/청소하는 튜브":               "부산 부산진구/맛집/청소하는 튜브",
    "서울/기라성":                       "서울 서초구/기라성",
    "서울/덕구아빠":                     "서울 성북/덕구아빠",
    "서울/세숑":                         "서울 종로구/맛집/세숑",
    "서울/철도노비":                     "서울 성동구/철도노비",
    "서울/호밀식빵":                     "서울/카페/호밀식빵",
    "안양/문둥":                         "경기 안양시 동안구/바다/문둥",
    "용인/음주흥무":                     "경기도 오산시/음주흥무",
    "원주시/노바디":                     "강원도 원주시/로컬맛집/노바디",
    "인천/감자깡":                       "인천논현동/맛집/감자깡",
    "인천/말랑콩떡":                     "인천 계양구/맛집/말랑콩떡",
    "인천/바두기":                       "인천남동구/바두기",
    "죽전/냉면과열면":                   "경기 용인시 기흥구/냉면과열면",
    "충북/소풍이":                       "충북청주/맛집/소풍이",
    "화성/OuO":                          "경기/화성/OuO",
    "경기/나루나":                       "경기 포천시/맛집/나루나",
    "경기/네오":                         "경기 화성 동탄구/로컬/네오",
    "경기/어퓨":                         "경기고양시/맛집/어퓨",
    "볼매/의정부":                       "서울 강북/맛집/볼매",
    "세종/잘 먹는 찡~":                  "충남 세종시/로컬/잘 먹는 찡~",
    "서울/driv":                         "용인/driv",
    "서울맛집 좋아":                     "서울 관악구/ 전국 맛집",
    "김포/연먹방":                       "인천 서구/연먹방",
    "경기/베개를 부비적대는 라이언":     "경기 남양주/맛집/라이언",
    "리인":                              "부산시 남구/리인",
    "비":                                "서울 비",
    "서울 / 빵이":                       "서울 빵이",
    "서울/프로도":                       "서울 강동/프로도",
    "일산/엄지척 제이지":               "경기파주/맛집/엄지척 제이지",
    "용인 수지구/네오":                  "경기도 용인시 수지구/ 뉴스/ 네오",
    # ── 동일인물 추정 (닉네임 키워드 유사) ──
    "포항/부끄러워하는 라이언":          "포항/맛집/곰덜",   # 포항 + 동일시간 메시지
}

# 신뢰도 표기용
NICK_MAP_CONFIDENCE = {
    "인천/woo": "확인",
    "당진&여수/뭉이도사": "확인",
    "군산&서울 송파,광진/닭국밥": "확인",
    "서울 성동구/ 먹기위해일한다": "확인",
    "인천 부평/딸기": "확인",
    "서울/냠냠": "확인",
    "경기양주 봉기": "확인",
    "미국 / 옴팡": "확인",
    "제주/소멍태": "확인",
}

def ampm_to_24h(ampm, h, m):
    if ampm == "오후" and h != 12:
        h += 12
    elif ampm == "오전" and h == 12:
        h = 0
    return h, m

def normalize_nick(nick: str) -> str:
    nick = nick.strip()
    return NICK_MAP.get(nick, nick)


# ─────────────────────────────────────────────────────────────
# 파서
# ─────────────────────────────────────────────────────────────

def parse_old_txt(filepath: str) -> tuple:
    """(이벤트 리스트, 발송자→마지막dt, 발송자→발송수)"""
    events, senders, msg_count = [], {}, defaultdict(int)
    EE = re.compile(r'^(\d{4})\. (\d+)\. (\d+)\. (오전|오후) (\d+):(\d+): (.+?)님이 (들어왔습니다|나갔습니다)\.$')
    MR = re.compile(r'^(\d{4})\. (\d+)\. (\d+)\. (오전|오후) (\d+):(\d+), (.+?) : (.+)$')
    try:
        with open(filepath, encoding="utf-8-sig") as f:
            for line in f:
                line = line.rstrip()
                m = EE.match(line)
                if m:
                    y,mo,d,ampm,hh,mm,nick,action = int(m[1]),int(m[2]),int(m[3]),m[4],int(m[5]),int(m[6]),m[7].strip(),m[8]
                    hh,mm = ampm_to_24h(ampm,hh,mm)
                    try: dt = datetime(y,mo,d,hh,mm)
                    except: continue
                    events.append({"dt":dt,"닉네임":nick,"이벤트":"입장" if action=="들어왔습니다" else "퇴장"})
                    continue
                m2 = MR.match(line)
                if m2:
                    y,mo,d,ampm,hh,mm,nick = int(m2[1]),int(m2[2]),int(m2[3]),m2[4],int(m2[5]),int(m2[6]),m2[7].strip()
                    hh,mm = ampm_to_24h(ampm,hh,mm)
                    try: dt = datetime(y,mo,d,hh,mm)
                    except: continue
                    if nick not in ("오픈채팅봇",):
                        msg_count[nick] += 1
                        if nick not in senders or dt > senders[nick]: senders[nick] = dt
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
    return events, senders, msg_count


def parse_eml(filepath: str) -> tuple:
    events, senders, msg_count = [], {}, defaultdict(int)
    EE = re.compile(r'^(\d{4})년 (\d+)월 (\d+)일 (오전|오후) (\d+):(\d+), (.+?)님이 (들어왔습니다|나갔습니다)\.$')
    MR = re.compile(r'^(\d{4})년 (\d+)월 (\d+)일 (오전|오후) (\d+):(\d+), (.+?) : (.+)$')
    try:
        with open(filepath, encoding="utf-8-sig") as f:
            for line in f:
                line = line.rstrip()
                m = EE.match(line)
                if m:
                    y,mo,d,ampm,hh,mm,nick,action = int(m[1]),int(m[2]),int(m[3]),m[4],int(m[5]),int(m[6]),m[7].strip(),m[8]
                    hh,mm = ampm_to_24h(ampm,hh,mm)
                    try: dt = datetime(y,mo,d,hh,mm)
                    except: continue
                    events.append({"dt":dt,"닉네임":nick,"이벤트":"입장" if action=="들어왔습니다" else "퇴장"})
                    continue
                m2 = MR.match(line)
                if m2:
                    y,mo,d,ampm,hh,mm,nick = int(m2[1]),int(m2[2]),int(m2[3]),m2[4],int(m2[5]),int(m2[6]),m2[7].strip()
                    hh,mm = ampm_to_24h(ampm,hh,mm)
                    try: dt = datetime(y,mo,d,hh,mm)
                    except: continue
                    if nick not in ("오픈채팅봇",):
                        msg_count[nick] += 1
                        if nick not in senders or dt > senders[nick]: senders[nick] = dt
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
    return events, senders, msg_count


def parse_bracket_txt(filepath: str) -> tuple:
    events, senders, msg_count = [], {}, defaultdict(int)
    MR = re.compile(r'^\[(.+?)\] \[(오전|오후) (\d+):(\d+)\] (.+)$')
    DR = re.compile(r'-+\s*(\d{4})년 (\d+)월 (\d+)일\s*\S+\s*-+')
    ER = re.compile(r'^(.+?)님이 들어왔습니다\.\s*$')
    XR = re.compile(r'^(.+?)님이 나갔습니다\.\s*$')
    cur = None
    try:
        with open(filepath, encoding="utf-8-sig") as f:
            for line in f:
                line = line.rstrip()
                dm = DR.match(line)
                if dm:
                    cur = (int(dm[1]),int(dm[2]),int(dm[3])); continue
                if cur is None: continue
                mm = MR.match(line)
                if mm:
                    nick,ampm,hh,mi = mm[1].strip(),mm[2],int(mm[3]),int(mm[4])
                    hh,mi = ampm_to_24h(ampm,hh,mi)
                    try: dt = datetime(cur[0],cur[1],cur[2],hh,mi)
                    except: continue
                    if nick not in ("오픈채팅봇",):
                        msg_count[nick] += 1
                        if nick not in senders or dt > senders[nick]: senders[nick] = dt
                    continue
                em = ER.match(line)
                if em:
                    events.append({"dt":datetime(cur[0],cur[1],cur[2]),"닉네임":em[1].strip(),"이벤트":"입장"}); continue
                xm = XR.match(line)
                if xm:
                    events.append({"dt":datetime(cur[0],cur[1],cur[2]),"닉네임":xm[1].strip(),"이벤트":"퇴장"})
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
    return events, senders, msg_count


# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("카카오톡 정보방 유저 추적 Excel 생성")
    print("=" * 60)

    f_2022  = os.path.join(INPUT_DIR, "220621~221231_대화기록.txt")
    f_2023  = os.path.join(INPUT_DIR, "230101~231231_대화기록.txt")
    f_2024  = os.path.join(INPUT_DIR, "240101~241231_대화기록.txt")
    f_2025a = os.path.join(INPUT_DIR, "250101~250304_대화기록.txt")
    f_2025i = os.path.join(INPUT_DIR, "250614~250729_정보방.txt")
    f_2026  = os.path.join(INPUT_DIR, "260517_대화기록.txt")
    f_eml   = os.path.join(INPUT_DIR, "현지인맛집,핫플,카페,현지인추천,여행코스공유🎉 74 카카오톡 대화.eml")

    print("\n[1단계] 파일 파싱...")
    all_events = []
    merged_senders = {}   # 현재닉네임 → 마지막 메시지 dt
    merged_msg_cnt = defaultdict(int)  # 현재닉네임 → 발송 수

    def add(evs, snd, cnt):
        for ev in evs:
            ev["현재닉네임"] = normalize_nick(ev["닉네임"])
        all_events.extend(evs)
        for nick, dt in snd.items():
            cn = normalize_nick(nick)
            if cn not in merged_senders or dt > merged_senders[cn]:
                merged_senders[cn] = dt
        for nick, c in cnt.items():
            cn = normalize_nick(nick)
            merged_msg_cnt[cn] += c

    for fp, label in [
        (f_2022,  "2022 txt"),
        (f_2023,  "2023 txt"),
        (f_2024,  "2024 txt"),
        (f_2025a, "2025a txt"),
    ]:
        evs, snd, cnt = parse_old_txt(fp)
        add(evs, snd, cnt)
        print(f"  {label}: 이벤트 {len(evs)}건, 발송자 {len(snd)}명")

    evs, snd, cnt = parse_bracket_txt(f_2025i)
    add(evs, snd, cnt)
    print(f"  2025 정보방 bracket: 이벤트 {len(evs)}건")

    evs, snd, cnt = parse_bracket_txt(f_2026)
    add(evs, snd, cnt)
    print(f"  260517 bracket: 이벤트 {len(evs)}건, 발송자 {len(snd)}명")

    evs, snd, cnt = parse_eml(f_eml)
    add(evs, snd, cnt)
    print(f"  EML 정보방: 이벤트 {len(evs)}건, 발송자 {len(snd)}명")

    # 이벤트 정렬
    all_events.sort(key=lambda e: e["dt"])
    print(f"\n  총 이벤트: {len(all_events)}건")

    # ─────────────────────────────────────────────────────────
    # [2단계] 현재닉네임 기준으로 유저 집계
    # ─────────────────────────────────────────────────────────
    print("\n[2단계] 유저 집계...")

    # 현재 방에 있는 유저: EML에서 마지막 상태로 판단
    eml_status = {}  # 현재닉 → True(있음)/False(나감)
    for ev in all_events:
        if "EML" in ev.get("이벤트","") or True:   # 모든 이벤트에서 추적
            pass
    # EML 파일만 따로 다시 파싱해서 최신 상태 파악
    eml_evs_raw, _, _ = parse_eml(f_eml)
    eml_evs_raw.sort(key=lambda e: e["dt"])
    for ev in eml_evs_raw:
        nick = ev["닉네임"]  # EML은 이미 현재 닉네임
        eml_status[nick] = (ev["이벤트"] == "입장")

    active_in_room = {n for n, active in eml_status.items() if active}
    print(f"  EML 기준 현재 방 멤버: {len(active_in_room)}명")

    # 유저별 이벤트 이력
    ud = defaultdict(lambda: {
        "이벤트목록": [],        # [(dt, 이벤트)]
        "과거닉네임": set(),
        "발송메시지수": 0,
        "마지막메시지일": None,
    })

    for ev in all_events:
        cn = ev["현재닉네임"]
        raw = ev["닉네임"]
        ud[cn]["이벤트목록"].append((ev["dt"], ev["이벤트"]))
        if raw != cn:
            ud[cn]["과거닉네임"].add(raw)

    for cn, c in merged_msg_cnt.items():
        ud[cn]["발송메시지수"] += c
        if cn in merged_senders:
            ud[cn]["마지막메시지일"] = merged_senders[cn]

    # ─────────────────────────────────────────────────────────
    # [3단계] 컬럼 계산
    # ─────────────────────────────────────────────────────────
    rows = []
    for cn, info in ud.items():
        evlist = sorted(info["이벤트목록"], key=lambda x: x[0])

        # 최초 입장일
        entries = [(dt, ev) for dt, ev in evlist if ev == "입장"]
        exits   = [(dt, ev) for dt, ev in evlist if ev == "퇴장"]

        first_entry = entries[0][0] if entries else None
        last_entry  = entries[-1][0] if entries else None
        last_exit   = exits[-1][0] if exits else None

        # 현재 방 여부: EML 기준 (닉네임 그대로인 경우) + 발송 기록
        in_room = (cn in active_in_room) or (cn in merged_senders and cn not in eml_status)
        # EML 명시적으로 나간 경우는 재확인
        if cn in eml_status and not eml_status[cn]:
            in_room = False
        # 메시지 보낸 사람은 방에 있었던 것
        # (최종 퇴장 이후 메시지가 없으면 나간 것)
        if last_exit and info["마지막메시지일"]:
            if info["마지막메시지일"] < last_exit:
                in_room = False

        # 총 입장 횟수
        total_entries = len(entries)

        # 재입장 여부 (2회 이상 입장)
        rejoined = total_entries >= 2

        # 강퇴 추정:
        # 입장 후 60분 이내 퇴장 + 메시지 발송 없음 = 강퇴 의심
        kick_suspected = False
        kick_count = 0
        for i, (edt, _) in enumerate(entries):
            # 이 입장 이후 다음 퇴장 찾기
            later_exits = [dt for dt, ev in exits if dt >= edt]
            if later_exits:
                next_exit = min(later_exits)
                delta = (next_exit - edt).total_seconds() / 60
                # 입장 후 30분 이내 퇴장, 이 입장 이후 보낸 메시지 없음
                if delta <= 30 and info["발송메시지수"] == 0:
                    kick_suspected = True
                    kick_count += 1

        # 닉네임 변경 횟수
        nick_change_count = len(info["과거닉네임"])

        rows.append({
            "현재닉네임":     cn,
            "과거닉네임":     ", ".join(sorted(info["과거닉네임"])) if info["과거닉네임"] else "",
            "닉네임변경횟수":  nick_change_count,
            "현재방여부":     "Y" if in_room else "N",
            "최초입장일시":   first_entry.strftime("%Y-%m-%d %H:%M") if first_entry else "",
            "최종입장일시":   last_entry.strftime("%Y-%m-%d %H:%M") if last_entry else "",
            "최종퇴장일시":   last_exit.strftime("%Y-%m-%d %H:%M") if last_exit else "",
            "강퇴추정":       f"의심({kick_count}회)" if kick_suspected else "",
            "총입장횟수":     total_entries,
            "재입장여부":     "Y" if rejoined else "N",
            "발송메시지수":   info["발송메시지수"],
            "마지막메시지일": info["마지막메시지일"].strftime("%Y-%m-%d") if info["마지막메시지일"] else "",
        })

    df_all = pd.DataFrame(rows)
    df_all = df_all.sort_values(
        ["현재방여부", "발송메시지수", "현재닉네임"],
        ascending=[False, False, True]
    ).reset_index(drop=True)

    print(f"  전체 유저: {len(df_all)}명")
    print(f"  현재 방 Y: {(df_all['현재방여부']=='Y').sum()}명")
    print(f"  재입장 있음: {(df_all['재입장여부']=='Y').sum()}명")
    print(f"  강퇴 의심: {(df_all['강퇴추정']!='').sum()}명")

    # ─────────────────────────────────────────────────────────
    # [4단계] 입퇴장 이력 시트
    # ─────────────────────────────────────────────────────────
    hist_rows = []
    for ev in all_events:
        cn = ev["현재닉네임"]
        hist_rows.append({
            "날짜":       ev["dt"].strftime("%Y-%m-%d"),
            "시간":       ev["dt"].strftime("%H:%M"),
            "닉네임(당시)": ev["닉네임"],
            "현재닉네임":  cn,
            "이벤트":     ev["이벤트"],
        })
    # 중복 제거
    seen = set()
    dedup_hist = []
    for r in hist_rows:
        k = (r["날짜"], r["시간"], r["현재닉네임"], r["이벤트"])
        if k not in seen:
            seen.add(k)
            dedup_hist.append(r)
    df_hist = pd.DataFrame(dedup_hist)
    print(f"  입퇴장 이벤트: {len(df_hist)}건 (중복제거 후)")

    # ─────────────────────────────────────────────────────────
    # [5단계] 닉네임_매핑 시트
    # ─────────────────────────────────────────────────────────
    map_rows = []
    # 사전 정의 매핑
    for old, new in sorted(NICK_MAP.items()):
        conf = NICK_MAP_CONFIDENCE.get(old, "추정")
        map_rows.append({"구형닉네임": old, "현재닉네임": new, "신뢰도": conf, "비고": ""})
    df_map = pd.DataFrame(map_rows)

    # ─────────────────────────────────────────────────────────
    # [6단계] 현재멤버 시트
    # ─────────────────────────────────────────────────────────
    df_current = df_all[df_all["현재방여부"] == "Y"].copy().reset_index(drop=True)

    # ─────────────────────────────────────────────────────────
    # [6.5단계] 퇴장자_목록 시트
    # 현재방여부=N + 입장 기록 있는 유저
    # 총입장횟수 10회 이상이면 카카오 기본캐릭터(공유닉) 가능성 표기
    # ─────────────────────────────────────────────────────────
    df_left = df_all[
        (df_all["현재방여부"] == "N") &
        (df_all["총입장횟수"] >= 1)
    ].copy()
    df_left = df_left.sort_values(
        ["총입장횟수", "최종퇴장일시"],
        ascending=[False, False]
    ).reset_index(drop=True)
    df_left["비고"] = df_left["총입장횟수"].apply(
        lambda n: "⚠ 카카오 기본캐릭터(동명이인 가능성)" if n >= 10 else ""
    )
    df_left = df_left[[
        "현재닉네임", "과거닉네임", "최초입장일시", "최종퇴장일시",
        "총입장횟수", "발송메시지수", "강퇴추정", "비고"
    ]]
    print(f"  퇴장자 목록: {len(df_left)}명")

    # ─────────────────────────────────────────────────────────
    # [6.6단계] 닉네임_미준수자 시트
    # 현재멤버 중 "지역/닉네임" 형식 미준수 (슬래시 없거나 앞부분이 지역명 아닌 경우)
    # ─────────────────────────────────────────────────────────
    def is_noncompliant(nick: str) -> bool:
        nick = nick.strip()
        if not nick or nick == "오픈채팅봇":
            return False
        # 슬래시 없으면 미준수
        if "/" not in nick:
            return True
        # 슬래시 앞부분(지역)이 너무 짧으면 의심 (1글자)
        region = nick.split("/")[0].strip()
        if len(region) <= 1:
            return True
        return False

    df_noncompliant = df_current[df_current["현재닉네임"].apply(is_noncompliant)].copy()
    df_noncompliant = df_noncompliant[["현재닉네임", "과거닉네임", "최초입장일시", "발송메시지수", "마지막메시지일"]].reset_index(drop=True)
    print(f"  닉네임 미준수자: {len(df_noncompliant)}명")

    # ─────────────────────────────────────────────────────────
    # [6.7단계] 장기_비활동멤버 시트
    # 현재멤버 중 마지막 메시지가 180일+ 전이거나 메시지 0건
    # ─────────────────────────────────────────────────────────
    today = datetime(2026, 5, 17)
    cutoff = today - timedelta(days=180)

    def is_inactive(row):
        if row["발송메시지수"] == 0:
            return True
        if not row["마지막메시지일"]:
            return True
        try:
            last = datetime.strptime(row["마지막메시지일"], "%Y-%m-%d")
            return last < cutoff
        except:
            return False

    df_inactive = df_current[df_current.apply(is_inactive, axis=1)].copy()
    df_inactive["비활동기간"] = df_inactive["마지막메시지일"].apply(
        lambda d: f"{(today - datetime.strptime(d, '%Y-%m-%d')).days}일" if d else "메시지없음"
    )
    df_inactive = df_inactive[["현재닉네임", "과거닉네임", "최초입장일시", "발송메시지수", "마지막메시지일", "비활동기간"]].sort_values("마지막메시지일").reset_index(drop=True)
    print(f"  장기 비활동 멤버: {len(df_inactive)}명")

    # ─────────────────────────────────────────────────────────
    # [6.8단계] 월별_추이 시트
    # 월별 입장/퇴장/순증감 집계
    # ─────────────────────────────────────────────────────────
    monthly_rows = []
    from collections import Counter
    entry_by_month = Counter()
    exit_by_month  = Counter()
    for r in dedup_hist:
        ym = r["날짜"][:7]  # "YYYY-MM"
        if r["이벤트"] == "입장":
            entry_by_month[ym] += 1
        else:
            exit_by_month[ym] += 1
    all_months = sorted(set(entry_by_month) | set(exit_by_month))
    for ym in all_months:
        e = entry_by_month[ym]
        x = exit_by_month[ym]
        monthly_rows.append({
            "연월": ym,
            "입장": e,
            "퇴장": x,
            "순증감": e - x,
        })
    df_monthly = pd.DataFrame(monthly_rows)
    print(f"  월별 추이: {len(df_monthly)}개월")

    # ─────────────────────────────────────────────────────────
    # [6.9단계] 강퇴_이력 시트
    # 강퇴 의심 유저 + 해당 입장/퇴장 시간 상세
    # ─────────────────────────────────────────────────────────
    kick_rows = []
    for cn, info in ud.items():
        evlist = sorted(info["이벤트목록"], key=lambda x: x[0])
        entries_k = [(dt, ev) for dt, ev in evlist if ev == "입장"]
        exits_k   = [(dt, ev) for dt, ev in evlist if ev == "퇴장"]
        for edt, _ in entries_k:
            later = [dt for dt, _ in exits_k if dt >= edt]
            if later:
                nxt = min(later)
                delta = (nxt - edt).total_seconds() / 60
                if delta <= 30 and info["발송메시지수"] == 0:
                    kick_rows.append({
                        "현재닉네임": cn,
                        "과거닉네임": ", ".join(sorted(info["과거닉네임"])) if info["과거닉네임"] else "",
                        "입장일시":   edt.strftime("%Y-%m-%d %H:%M"),
                        "퇴장일시":   nxt.strftime("%Y-%m-%d %H:%M"),
                        "체류시간(분)": round(delta, 1),
                        "발송메시지수": info["발송메시지수"],
                    })
    df_kick = pd.DataFrame(kick_rows).sort_values("입장일시", ascending=False).reset_index(drop=True)
    print(f"  강퇴 의심 이력: {len(df_kick)}건")

    # ─────────────────────────────────────────────────────────
    # [7단계] Excel 저장
    # ─────────────────────────────────────────────────────────
    print(f"\n[5단계] Excel 저장: {OUTPUT_XLSX}")
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df_current.to_excel(writer, sheet_name="현재멤버", index=False)
        df_all.to_excel(writer, sheet_name="유저_전체목록", index=False)
        df_left.to_excel(writer, sheet_name="퇴장자_목록", index=False)
        df_noncompliant.to_excel(writer, sheet_name="닉네임_미준수자", index=False)
        df_inactive.to_excel(writer, sheet_name="장기_비활동멤버", index=False)
        df_monthly.to_excel(writer, sheet_name="월별_추이", index=False)
        df_kick.to_excel(writer, sheet_name="강퇴_이력", index=False)
        df_hist.to_excel(writer, sheet_name="입퇴장_이력", index=False)
        df_map.to_excel(writer, sheet_name="닉네임_매핑", index=False)

        # 열너비 자동조정
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max((len(str(cell.value or "")) for cell in col), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

    print("  완료!")

    # ─────────────────────────────────────────────────────────
    # [8단계] 운영_리포트.xlsx — 2022-06-21 ~ 현재 전체 이력
    # ─────────────────────────────────────────────────────────
    print(f"\n[8단계] 운영 리포트 저장: {OUTPUT_REPORT}")

    # ── 요약 시트 ──────────────────────────────────────────
    open_date = datetime(2022, 6, 21)
    op_days   = (today - open_date).days
    summary_rows = [
        {"항목": "운영 시작일",       "값": open_date.strftime("%Y-%m-%d")},
        {"항목": "리포트 기준일",     "값": today.strftime("%Y-%m-%d")},
        {"항목": "운영 기간",         "값": f"{op_days}일 ({op_days//365}년 {(op_days%365)//30}개월)"},
        {"항목": "누적 유입 인원",    "값": len(df_all)},
        {"항목": "현재 방 인원",      "값": (df_all["현재방여부"]=="Y").sum()},
        {"항목": "총 퇴장 인원",      "값": (df_all["현재방여부"]=="N").sum()},
        {"항목": "강퇴 의심 건수",    "값": len(df_kick)},
        {"항목": "닉네임 미준수자",   "값": len(df_noncompliant)},
        {"항목": "장기 비활동 멤버",  "값": len(df_inactive)},
        {"항목": "재입장 유저",       "값": (df_all["재입장여부"]=="Y").sum()},
    ]
    df_summary = pd.DataFrame(summary_rows)

    # ── 월별 운영 요약 ─────────────────────────────────────
    # 신규입장 = 해당월이 최초입장월인 유저 수
    first_entry_by_month = Counter()
    for _, row in df_all.iterrows():
        if row["최초입장일시"]:
            ym = str(row["최초입장일시"])[:7]
            first_entry_by_month[ym] += 1

    kick_by_month = Counter()
    for _, row in df_kick.iterrows():
        ym = str(row["입장일시"])[:7]
        kick_by_month[ym] += 1

    all_ym = sorted(set(entry_by_month) | set(exit_by_month) | set(first_entry_by_month))
    cumulative = 0
    monthly_report = []
    for ym in all_ym:
        new_m  = first_entry_by_month[ym]
        exit_m = exit_by_month[ym]
        cumulative += new_m - exit_m
        monthly_report.append({
            "연월":         ym,
            "신규유입":     new_m,
            "퇴장":         exit_m,
            "강퇴의심":     kick_by_month[ym],
            "순증감":       new_m - exit_m,
            "누적멤버(추정)": max(cumulative, 0),
        })
    df_monthly_report = pd.DataFrame(monthly_report)

    # ── 신규 입장자 전체 (최초 입장일 기준) ───────────────
    new_members_rows = df_all[df_all["최초입장일시"] != ""].copy()
    new_members_rows = new_members_rows.sort_values("최초입장일시")[
        ["최초입장일시", "현재닉네임", "과거닉네임", "현재방여부", "발송메시지수", "마지막메시지일"]
    ].reset_index(drop=True)

    # ── 퇴장 이력 전체 ────────────────────────────────────
    exit_hist_rows = []
    for r in dedup_hist:
        if r["이벤트"] == "퇴장":
            exit_hist_rows.append({
                "날짜":        r["날짜"],
                "시간":        r["시간"],
                "현재닉네임":  r["현재닉네임"],
                "닉네임(당시)": r["닉네임(당시)"],
            })
    df_exit_hist = pd.DataFrame(exit_hist_rows).sort_values(["날짜","시간"]).reset_index(drop=True)

    # ── 강퇴 의심 전체 (입장일 오름차순) ─────────────────
    df_kick_report = df_kick.sort_values("입장일시").reset_index(drop=True)

    with pd.ExcelWriter(OUTPUT_REPORT, engine="openpyxl") as writer:
        df_summary.to_excel(writer,        sheet_name="전체_요약",     index=False)
        df_monthly_report.to_excel(writer, sheet_name="월별_운영요약", index=False)
        new_members_rows.to_excel(writer,  sheet_name="신규입장자_전체", index=False)
        df_exit_hist.to_excel(writer,      sheet_name="퇴장이력_전체", index=False)
        df_kick_report.to_excel(writer,    sheet_name="강퇴의심_전체", index=False)
        df_noncompliant.to_excel(writer,   sheet_name="닉네임_위반자", index=False)
        df_inactive.to_excel(writer,       sheet_name="장기_비활동",   index=False)

        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max((len(str(cell.value or "")) for cell in col), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

    print("  완료!")

    # ─────────────────────────────────────────────────────────
    # [9단계] 닉네임_매핑.xlsx
    # ─────────────────────────────────────────────────────────
    print(f"\n[9단계] 닉네임 매핑 저장: {OUTPUT_NICKMAP}")

    # 사전 정의 매핑
    defined_rows = []
    for old, new in sorted(NICK_MAP.items()):
        conf = NICK_MAP_CONFIDENCE.get(old, "추정")
        defined_rows.append({"구형닉네임": old, "현재닉네임": new, "신뢰도": conf, "비고": ""})
    df_nickmap_defined = pd.DataFrame(defined_rows)

    # 자동 발견 매핑: 과거닉네임이 있는 유저 목록 (NICK_MAP에 없는 것)
    auto_rows = []
    for _, row in df_all.iterrows():
        if not row["과거닉네임"]:
            continue
        for old_nick in row["과거닉네임"].split(", "):
            old_nick = old_nick.strip()
            if old_nick and old_nick not in NICK_MAP:
                auto_rows.append({
                    "구형닉네임": old_nick,
                    "현재닉네임": row["현재닉네임"],
                    "신뢰도": "자동발견",
                    "비고": "",
                })
    cols_auto = ["구형닉네임", "현재닉네임", "신뢰도", "비고"]
    df_nickmap_auto = (pd.DataFrame(auto_rows, columns=cols_auto) if auto_rows else pd.DataFrame(columns=cols_auto))
    df_nickmap_auto = df_nickmap_auto.drop_duplicates("구형닉네임").sort_values("구형닉네임").reset_index(drop=True)

    # 닉네임 변경 이력: 유저별로 과거→현재 타임라인
    timeline_rows = []
    for _, row in df_all[df_all["과거닉네임"] != ""].iterrows():
        timeline_rows.append({
            "현재닉네임":    row["현재닉네임"],
            "과거닉네임":    row["과거닉네임"],
            "닉네임변경횟수": row["닉네임변경횟수"],
            "최초입장일시":  row["최초입장일시"],
            "현재방여부":    row["현재방여부"],
        })
    df_timeline = pd.DataFrame(timeline_rows).sort_values("닉네임변경횟수", ascending=False).reset_index(drop=True)

    with pd.ExcelWriter(OUTPUT_NICKMAP, engine="openpyxl") as writer:
        df_nickmap_defined.to_excel(writer, sheet_name="확인된_매핑", index=False)
        df_nickmap_auto.to_excel(writer,    sheet_name="자동발견_매핑", index=False)
        df_timeline.to_excel(writer,        sheet_name="변경이력_유저별", index=False)

        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max((len(str(cell.value or "")) for cell in col), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

    print("  완료!")
    print("\n전체 완료!")


if __name__ == "__main__":
    main()
