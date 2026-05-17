#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카카오톡 오픈채팅 대화기록 분석 및 연단위 파일 생성 스크립트
"""

import re
import os
from collections import defaultdict
from datetime import datetime
import pandas as pd

BASE_DIR = "/mnt/c/Users/ryu53/Downloads/깃허브/harness-main/놀생_오픈카톡방"
INPUT_DIR = os.path.join(BASE_DIR, "대화기록", "원본")
OUTPUT_DIR = os.path.join(BASE_DIR, "대화기록", "정제본")
DATA_DIR = os.path.join(BASE_DIR, "데이터")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 사전 정의된 닉네임 매핑 (구형 → 현재)
# ─────────────────────────────────────────────────────────────
KNOWN_MAPPING = {
    "인천/woo": "서울/응원하는 라이언",
    "당진&여수/뭉이도사": "충남당진&전남여수/전국구맛집/뭉이",
    "충남/당진&전남/여수/뭉이": "충남당진&전남여수/전국구맛집/뭉이",
    "당진/뭉이도사": "충남당진&전남여수/전국구맛집/뭉이",
    "군산&서울 송파,광진/닭국밥": "전북 군산&서울 송파/로컬여행/닭국밥",
    "군산&서울/닭국밥": "전북 군산&서울 송파/로컬여행/닭국밥",
    "서울 성동구/ 먹기위해일한다": "경기 고양 일산동구/로컬맛집/먹위일",
    "서울성동구/먹기위해일한다": "경기 고양 일산동구/로컬맛집/먹위일",
    "서울/먹기위해일한다": "경기 고양 일산동구/로컬맛집/먹위일",
    "인천 부평/딸기": "리본/인천",
    "인천/딸기": "리본/인천",
    "서울/냠냠": "서울 강남구/냠냠",
    "경기양주 봉기": "경기양주/ 봉기",
    "양주 봉기": "경기양주/ 봉기",
    "양주/봉기": "경기양주/ 봉기",
    "미국 / 옴팡": "해외미국/옴팡",
    "미국/옴팡": "해외미국/옴팡",
    "제주/소멍태": "제주도 제주시/올레길, 맛집/소멍태",
    "전주/무한": "전북 전주시 완산구/사진&맛집/ 무한",
    "서울/루팡": "서울 강동구/루팡",
    "서울/개별이": "서울/개별이",
    "서울/갈매서운기": "서울/갈매서운기",
    "창원/블루": "창원/블루",
}

# ─────────────────────────────────────────────────────────────
# 파싱 함수
# ─────────────────────────────────────────────────────────────

def ampm_to_24h(ampm: str, h: int, m: int):
    """오전/오후 시간을 24시간제로 변환"""
    if ampm == "오후" and h != 12:
        h += 12
    elif ampm == "오전" and h == 12:
        h = 0
    return h, m


class Message:
    """통일된 메시지 객체"""
    __slots__ = ("dt", "nickname", "text", "source_file")

    def __init__(self, dt: datetime, nickname: str, text: str, source_file: str = ""):
        self.dt = dt
        self.nickname = nickname
        self.text = text
        self.source_file = source_file

    def dedup_key(self):
        """중복 제거용 키 (시간 1분 단위 + 닉네임 일부 + 메시지 앞 30자)"""
        nick_norm = re.sub(r'\s+', '', self.nickname)[:20]
        txt_norm = re.sub(r'\s+', '', self.text)[:30]
        return (self.dt.year, self.dt.month, self.dt.day,
                self.dt.hour, self.dt.minute, nick_norm, txt_norm)

    def format_line(self) -> str:
        dt_str = self.dt.strftime("%Y-%m-%d %H:%M")
        return f"[{dt_str}] {self.nickname}: {self.text}"


def parse_old_txt(filepath: str) -> list:
    """
    구형 포맷: 2022. 6. 21. 오후 5:54, 닉네임 : 메시지
    입장/퇴장: 2022. 6. 21. 오후 8:33: 퇴근하는 프로도님이 들어왔습니다.
    날짜 헤더: 2022년 6월 21일 화요일
    """
    msgs = []
    # 메시지 라인 패턴
    MSG_RE = re.compile(
        r'^(\d{4})\. (\d+)\. (\d+)\. (오전|오후) (\d+):(\d+), (.+?) : (.+)$'
    )
    # 입장/퇴장 패턴
    ENTER_EXIT_RE = re.compile(
        r'^(\d{4})\. (\d+)\. (\d+)\. (오전|오후) (\d+):(\d+): (.+님이 (?:들어왔습니다|나갔습니다)\.)$'
    )
    fname = os.path.basename(filepath)

    try:
        with open(filepath, encoding="utf-8-sig") as f:
            for line in f:
                line = line.rstrip('\n').rstrip('\r')
                m = MSG_RE.match(line)
                if m:
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    ampm, hh, mm = m.group(4), int(m.group(5)), int(m.group(6))
                    nick = m.group(7).strip()
                    text = m.group(8).strip()
                    hh, mm = ampm_to_24h(ampm, hh, mm)
                    try:
                        dt = datetime(y, mo, d, hh, mm)
                    except ValueError:
                        continue
                    msgs.append(Message(dt, nick, text, fname))
                    continue
                m2 = ENTER_EXIT_RE.match(line)
                if m2:
                    y, mo, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
                    ampm, hh, mm = m2.group(4), int(m2.group(5)), int(m2.group(6))
                    text = m2.group(7).strip()
                    hh, mm = ampm_to_24h(ampm, hh, mm)
                    try:
                        dt = datetime(y, mo, d, hh, mm)
                    except ValueError:
                        continue
                    msgs.append(Message(dt, "__system__", text, fname))
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
    return msgs


def parse_eml(filepath: str) -> list:
    """
    EML 포맷:
    2023년 10월 4일 오전 10:50, 닉네임 : 메시지
    2023년 10월 4일 오전 10:45, 닉네임님이 들어왔습니다.
    """
    msgs = []
    MSG_RE = re.compile(
        r'^(\d{4})년 (\d+)월 (\d+)일 (오전|오후) (\d+):(\d+), (.+?) : (.+)$'
    )
    ENTER_EXIT_RE = re.compile(
        r'^(\d{4})년 (\d+)월 (\d+)일 (오전|오후) (\d+):(\d+), (.+님이 (?:들어왔습니다|나갔습니다)\.)$'
    )
    fname = os.path.basename(filepath)

    try:
        with open(filepath, encoding="utf-8-sig") as f:
            for line in f:
                line = line.rstrip('\n').rstrip('\r')
                m = MSG_RE.match(line)
                if m:
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    ampm, hh, mm = m.group(4), int(m.group(5)), int(m.group(6))
                    nick = m.group(7).strip()
                    text = m.group(8).strip()
                    hh, mm = ampm_to_24h(ampm, hh, mm)
                    try:
                        dt = datetime(y, mo, d, hh, mm)
                    except ValueError:
                        continue
                    msgs.append(Message(dt, nick, text, fname))
                    continue
                m2 = ENTER_EXIT_RE.match(line)
                if m2:
                    y, mo, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
                    ampm, hh, mm = m2.group(4), int(m2.group(5)), int(m2.group(6))
                    text = m2.group(7).strip()
                    hh, mm = ampm_to_24h(ampm, hh, mm)
                    try:
                        dt = datetime(y, mo, d, hh, mm)
                    except ValueError:
                        continue
                    msgs.append(Message(dt, "__system__", text, fname))
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
    return msgs


def parse_bracket_txt(filepath: str) -> list:
    """
    새 브래킷 포맷:
    [닉네임] [오전 9:04] 메시지
    날짜 구분선: --------------- 2025년 6월 14일 토요일 ---------------
    입장/퇴장: 닉네임님이 들어왔습니다.
    """
    msgs = []
    MSG_RE = re.compile(r'^\[(.+?)\] \[(오전|오후) (\d+):(\d+)\] (.+)$')
    DATE_RE = re.compile(r'-+\s*(\d{4})년 (\d+)월 (\d+)일\s*\S+\s*-+')
    ENTER_EXIT_RE = re.compile(r'^(.+님이 (?:들어왔습니다|나갔습니다)\.)\s*$')
    fname = os.path.basename(filepath)

    current_date = None
    try:
        with open(filepath, encoding="utf-8-sig") as f:
            for line in f:
                line = line.rstrip('\n').rstrip('\r')
                dm = DATE_RE.match(line)
                if dm:
                    current_date = (int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                    continue
                mm = MSG_RE.match(line)
                if mm and current_date:
                    nick = mm.group(1).strip()
                    ampm, hh, mi = mm.group(2), int(mm.group(3)), int(mm.group(4))
                    text = mm.group(5).strip()
                    hh, mi = ampm_to_24h(ampm, hh, mi)
                    try:
                        dt = datetime(current_date[0], current_date[1], current_date[2], hh, mi)
                    except ValueError:
                        continue
                    msgs.append(Message(dt, nick, text, fname))
                    continue
                em = ENTER_EXIT_RE.match(line)
                if em and current_date:
                    text = em.group(1).strip()
                    # 시간 없으므로 00:00 으로 처리 (단, 뒤 메시지 시간 추정 불가)
                    try:
                        dt = datetime(current_date[0], current_date[1], current_date[2], 0, 0)
                    except ValueError:
                        continue
                    msgs.append(Message(dt, "__system__", text, fname))
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
    return msgs


# ─────────────────────────────────────────────────────────────
# 닉네임 매핑 자동 발견
# ─────────────────────────────────────────────────────────────

SKIP_TEXTS = {"이모티콘", "사진", "삭제된 메시지입니다.", "동영상", "파일", "연락처", "지도", "투표"}

def auto_discover_mappings(old_msgs: list, eml_msgs: list) -> dict:
    """
    같은 (year, month, day, hour, minute, message_snippet) 쌍에서
    nickname이 다르면 매핑으로 추가.
    오픈채팅봇, 짧은/공통 메시지는 제외.
    """
    EXCLUDED_NICKS = {"오픈채팅봇", "__system__"}

    # EML 인덱스 구성 (닉네임별 고유 키 카운트 - 동일 시간에 여러 명이면 스킵)
    eml_index = {}
    eml_key_count = defaultdict(int)
    for msg in eml_msgs:
        if msg.nickname in EXCLUDED_NICKS:
            continue
        txt = re.sub(r'\s+', '', msg.text)
        if len(txt) < 5 or txt in SKIP_TEXTS or txt.startswith("사진") or txt.startswith("이모티콘"):
            continue
        snippet = txt[:30]
        key = (msg.dt.year, msg.dt.month, msg.dt.day, msg.dt.hour, msg.dt.minute, snippet)
        eml_key_count[key] += 1
        eml_index[key] = msg.nickname

    discovered = {}
    for msg in old_msgs:
        if msg.nickname in EXCLUDED_NICKS:
            continue
        txt = re.sub(r'\s+', '', msg.text)
        if len(txt) < 5 or txt in SKIP_TEXTS or txt.startswith("사진") or txt.startswith("이모티콘"):
            continue
        snippet = txt[:30]
        key = (msg.dt.year, msg.dt.month, msg.dt.day, msg.dt.hour, msg.dt.minute, snippet)
        # 동일 키에 EML에서 2명 이상이면 애매하므로 스킵
        if key in eml_index and eml_key_count[key] == 1:
            eml_nick = eml_index[key]
            old_nick = msg.nickname
            if (old_nick != eml_nick
                    and old_nick not in KNOWN_MAPPING
                    and eml_nick not in EXCLUDED_NICKS
                    and old_nick not in EXCLUDED_NICKS):
                if old_nick not in discovered:
                    discovered[old_nick] = eml_nick
                    print(f"  [자동발견] '{old_nick}' → '{eml_nick}'")
    return discovered


def normalize_nick(nick: str, mapping: dict) -> str:
    """닉네임을 현재 닉네임으로 변환"""
    if nick == "__system__":
        return nick
    # 정확히 일치하는 경우
    if nick in mapping:
        return mapping[nick]
    # 공백 제거 후 비교
    nick_stripped = nick.strip()
    if nick_stripped in mapping:
        return mapping[nick_stripped]
    return nick


# ─────────────────────────────────────────────────────────────
# 현재 방에 있는 사람 목록 수집 (EML에서)
# ─────────────────────────────────────────────────────────────

def collect_active_members(eml_msgs: list) -> set:
    """EML의 마지막 상태 기준으로 방에 있는 닉네임 집합"""
    status = {}  # nick → True(있음) / False(나감)
    for msg in eml_msgs:
        if msg.nickname == "__system__":
            text = msg.text
            nm = re.match(r'^(.+)님이 (들어왔습니다|나갔습니다)\.', text)
            if nm:
                nick, action = nm.group(1), nm.group(2)
                status[nick] = (action == "들어왔습니다")
    return {n for n, active in status.items() if active}


# ─────────────────────────────────────────────────────────────
# 중복 제거 + 정렬 + 출력
# ─────────────────────────────────────────────────────────────

def dedup_and_sort(msgs: list) -> list:
    seen = set()
    result = []
    for msg in sorted(msgs, key=lambda m: m.dt):
        k = msg.dedup_key()
        if k not in seen:
            seen.add(k)
            result.append(msg)
    return result


def write_messages(msgs: list, out_path: str, mapping: dict):
    """닉네임 치환 후 파일 저장"""
    msgs = dedup_and_sort(msgs)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        current_date = None
        for msg in msgs:
            date_str = msg.dt.strftime("%Y년 %m월 %d일")
            if date_str != current_date:
                f.write(f"\n--- {date_str} ---\n")
                current_date = date_str
            nick = normalize_nick(msg.nickname, mapping)
            if nick == "__system__":
                f.write(f"  [{msg.text}]\n")
            else:
                time_str = msg.dt.strftime("%H:%M")
                f.write(f"[{time_str}] {nick}: {msg.text}\n")
    print(f"  => 저장: {out_path} ({len(msgs)} 줄)")


# ─────────────────────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("카카오톡 대화기록 분석 시작")
    print("=" * 60)

    # 파일 경로
    f_2022 = os.path.join(INPUT_DIR, "220621~221231_대화기록.txt")
    f_2023 = os.path.join(INPUT_DIR, "230101~231231_대화기록.txt")
    f_2024 = os.path.join(INPUT_DIR, "240101~241231_대화기록.txt")
    f_2025a = os.path.join(INPUT_DIR, "250101~250304_대화기록.txt")
    f_2025_info = os.path.join(INPUT_DIR, "250614~250729_정보방.txt")
    f_2025_suda = os.path.join(INPUT_DIR, "250614~250729_수다방.txt")
    f_2026 = os.path.join(INPUT_DIR, "260517_대화기록.txt")
    f_eml_info = os.path.join(INPUT_DIR, "현지인맛집,핫플,카페,현지인추천,여행코스공유🎉 74 카카오톡 대화.eml")
    f_eml_suda = os.path.join(INPUT_DIR, "맛집,핫플,카페,가볼만한곳,여행코스공유_수다_모임_벙 12 님과 카카오톡 대화.eml")

    print("\n[1단계] 파일 파싱...")
    msgs_2022 = parse_old_txt(f_2022)
    msgs_2023 = parse_old_txt(f_2023)
    msgs_2024 = parse_old_txt(f_2024)
    msgs_2025a = parse_old_txt(f_2025a)
    msgs_2025_info = parse_bracket_txt(f_2025_info)
    msgs_2025_suda = parse_bracket_txt(f_2025_suda)
    msgs_2026_bracket = parse_bracket_txt(f_2026)
    msgs_eml_info = parse_eml(f_eml_info)
    msgs_eml_suda = parse_eml(f_eml_suda)

    print(f"  2022 txt: {len(msgs_2022)} 메시지")
    print(f"  2023 txt: {len(msgs_2023)} 메시지")
    print(f"  2024 txt: {len(msgs_2024)} 메시지")
    print(f"  2025a txt: {len(msgs_2025a)} 메시지")
    print(f"  2025 정보방 bracket: {len(msgs_2025_info)} 메시지")
    print(f"  2025 수다방 bracket: {len(msgs_2025_suda)} 메시지")
    print(f"  260517 bracket: {len(msgs_2026_bracket)} 메시지")
    print(f"  EML 정보방: {len(msgs_eml_info)} 메시지")
    print(f"  EML 수다방: {len(msgs_eml_suda)} 메시지")

    print("\n[2단계] 닉네임 매핑 자동 발견...")
    # 2024 txt + EML 정보방에서 자동 발견
    auto_map = auto_discover_mappings(msgs_2024, msgs_eml_info)
    # 2023 txt에서도 추가 시도
    auto_map2 = auto_discover_mappings(msgs_2023, msgs_eml_info)
    auto_map.update(auto_map2)

    # 통합 매핑
    full_mapping = dict(KNOWN_MAPPING)
    full_mapping.update(auto_map)

    print(f"\n  전체 매핑 수: {len(full_mapping)}")

    # 현재 방 멤버
    active_info = collect_active_members(msgs_eml_info)
    active_suda = collect_active_members(msgs_eml_suda)
    print(f"  정보방 현재 멤버: {len(active_info)}명")
    print(f"  수다방 현재 멤버: {len(active_suda)}명")

    # ───────────────────────────────────────────────────────
    # EML에서 연도별 분리
    # ───────────────────────────────────────────────────────
    def filter_year(msgs, year):
        return [m for m in msgs if m.dt.year == year]

    def filter_month_range(msgs, year, month_start, month_end):
        return [m for m in msgs if m.dt.year == year and month_start <= m.dt.month <= month_end]

    # ───────────────────────────────────────────────────────
    # 2023 txt: Jan~Sep (EML은 Oct~Dec만 있음)
    # 2023 분기: txt Jan-Sep + EML Oct-Dec
    # ───────────────────────────────────────────────────────
    msgs_2023_txt_jansep = filter_month_range(msgs_2023, 2023, 1, 9)
    msgs_2023_eml_octdec = filter_year(msgs_eml_info, 2023)
    # txt Oct-Dec도 포함 (EML에 없는 내용 보완)
    msgs_2023_txt_octdec = filter_month_range(msgs_2023, 2023, 10, 12)

    print("\n[3단계] 연단위 파일 생성...")

    # 2022_대화기록.txt
    write_messages(msgs_2022, os.path.join(OUTPUT_DIR, "2022_대화기록.txt"), full_mapping)

    # 2023_대화기록.txt (txt Jan-Sep + txt Oct-Dec + EML Oct-Dec 통합, 중복제거)
    msgs_2023_all = msgs_2023_txt_jansep + msgs_2023_txt_octdec + msgs_2023_eml_octdec
    write_messages(msgs_2023_all, os.path.join(OUTPUT_DIR, "2023_대화기록.txt"), full_mapping)

    # 2024_대화기록.txt — EML만 사용 (EML이 2023-10 ~ 2026-05 전체 커버, 현재 닉네임)
    msgs_2024_eml = filter_year(msgs_eml_info, 2024)
    write_messages(msgs_2024_eml, os.path.join(OUTPUT_DIR, "2024_대화기록.txt"), full_mapping)

    # 2025_대화기록_정보방.txt — EML + 260517 bracket 2025 부분 통합
    msgs_2025_eml_info = filter_year(msgs_eml_info, 2025)
    msgs_2025_bracket_info = filter_year(msgs_2026_bracket, 2025)
    write_messages(msgs_2025_eml_info + msgs_2025_bracket_info, os.path.join(OUTPUT_DIR, "2025_대화기록_정보방.txt"), full_mapping)

    # 2025_대화기록_수다방.txt — 수다방 EML만 사용 (2025년)
    msgs_2025_eml_suda = filter_year(msgs_eml_suda, 2025)
    write_messages(msgs_2025_eml_suda, os.path.join(OUTPUT_DIR, "2025_대화기록_수다방.txt"), full_mapping)

    # 2026_대화기록_정보방.txt — EML + 260517 bracket 2026 부분 통합
    msgs_2026_eml_info = filter_year(msgs_eml_info, 2026)
    msgs_2026_bracket_info = filter_year(msgs_2026_bracket, 2026)
    write_messages(msgs_2026_eml_info + msgs_2026_bracket_info, os.path.join(OUTPUT_DIR, "2026_대화기록_정보방.txt"), full_mapping)

    # 2026_대화기록_수다방.txt — 수다방 EML (2026년)
    msgs_2026_eml_suda = filter_year(msgs_eml_suda, 2026)
    write_messages(msgs_2026_eml_suda, os.path.join(OUTPUT_DIR, "2026_대화기록_수다방.txt"), full_mapping)

    # ───────────────────────────────────────────────────────
    # 닉네임 매핑 저장
    # ───────────────────────────────────────────────────────
    print("\n[4단계] 닉네임 매핑 파일 저장...")
    os.makedirs(DATA_DIR, exist_ok=True)
    mapping_path = os.path.join(DATA_DIR, "닉네임_매핑.txt")

    # 구형 닉네임의 현재 상태 판별
    # active_info에 현재 닉네임이 있으면 현재 방에 있음
    all_current_nicks = set(active_info) | set(active_suda)

    with open(mapping_path, "w", encoding="utf-8") as f:
        f.write("# 카카오톡 닉네임 매핑 (구형 → 현재)\n")
        f.write(f"# 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        f.write("[사전 정의된 매핑]\n")
        for old, new in sorted(KNOWN_MAPPING.items()):
            status = "현재방에있음" if new in all_current_nicks else "나감/불명"
            f.write(f"  {old} → {new} [{status}]\n")

        if auto_map:
            f.write("\n[자동 발견된 매핑]\n")
            for old, new in sorted(auto_map.items()):
                status = "현재방에있음" if new in all_current_nicks else "나감/불명"
                f.write(f"  {old} → {new} [{status}]\n")

        f.write("\n[전체 현재 정보방 멤버]\n")
        for nick in sorted(active_info):
            f.write(f"  {nick}\n")

        f.write("\n[전체 현재 수다방 멤버]\n")
        for nick in sorted(active_suda):
            f.write(f"  {nick}\n")

    print(f"  => 저장: {mapping_path}")

    # Excel 저장
    xlsx_path = os.path.join(DATA_DIR, "닉네임_매핑.xlsx")
    print(f"\n[5단계] 닉네임 매핑 Excel 저장: {xlsx_path}")

    # 시트1: 사전정의_매핑
    rows_known = []
    for old, new in sorted(KNOWN_MAPPING.items()):
        status = "현재방에있음" if new in all_current_nicks else "나감/불명"
        rows_known.append({"구형닉네임": old, "현재닉네임": new, "상태": status})

    # 시트2: 자동발견_매핑
    rows_auto = []
    for old, new in sorted(auto_map.items()):
        status = "현재방에있음" if new in all_current_nicks else "나감/불명"
        rows_auto.append({"구형닉네임": old, "현재닉네임": new, "상태": status})

    # 시트3: 전체 매핑 (사전정의 + 자동발견)
    rows_all_map = rows_known + [dict(r, **{"구분": "자동발견"}) for r in rows_auto]
    for r in rows_known:
        r["구분"] = "사전정의"

    # 시트4,5: 현재 멤버
    rows_info = [{"닉네임": n} for n in sorted(active_info)]
    rows_suda = [{"닉네임": n} for n in sorted(active_suda)]

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame(rows_known).to_excel(writer, sheet_name="사전정의_매핑", index=False)
        pd.DataFrame(rows_auto).to_excel(writer, sheet_name="자동발견_매핑", index=False)
        pd.DataFrame(rows_info).to_excel(writer, sheet_name="현재_정보방멤버", index=False)
        pd.DataFrame(rows_suda).to_excel(writer, sheet_name="현재_수다방멤버", index=False)
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max((len(str(cell.value or "")) for cell in col), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)
    print(f"  => 저장 완료")

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)

    # 결과 요약 출력
    print("\n[전체 닉네임 매핑 목록]")
    for old, new in sorted(full_mapping.items()):
        status = "현재방에있음" if new in all_current_nicks else "나감/불명"
        print(f"  {old!r} → {new!r} [{status}]")

    print(f"\n[생성된 파일]")
    for fn in sorted(os.listdir(OUTPUT_DIR)):
        fpath = os.path.join(OUTPUT_DIR, fn)
        sz = os.path.getsize(fpath)
        print(f"  {fn} ({sz:,} bytes)")


if __name__ == "__main__":
    main()
