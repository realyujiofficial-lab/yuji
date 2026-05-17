#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주간 오카방 운영 리포트 자동 생성
실행: python3 weekly_report.py
      python3 weekly_report.py --week 2026-05-12  (특정 주 월요일 지정)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS_JSON = os.path.join(BASE_DIR, "_workspace", "stats.json")
REPORT_DIR = os.path.join(BASE_DIR, "운영", "주간리포트")
ISSUE_DIR  = os.path.join(BASE_DIR, "운영", "이슈")

os.makedirs(REPORT_DIR, exist_ok=True)


def parse_korean_date(s: str) -> datetime:
    s = s.replace("년 ", "-").replace("월 ", "-").replace("일", "").strip()
    return datetime.strptime(s, "%Y-%m-%d")


def korean_date(dt: datetime) -> str:
    return dt.strftime("%Y년 %m월 %d일")


def get_week_range(anchor: datetime = None):
    """anchor 기준 월~일 반환. anchor 없으면 가장 최근 완료된 주."""
    if anchor:
        mon = anchor - timedelta(days=anchor.weekday())
    else:
        today = datetime.today()
        mon = today - timedelta(days=today.weekday() + 7)
    sun = mon + timedelta(days=6)
    return mon, sun


def weekday_kr(dt: datetime) -> str:
    return ["월", "화", "수", "목", "금", "토", "일"][dt.weekday()]


def load_issues_this_week(mon: datetime, sun: datetime) -> list[dict]:
    issues = []
    if not os.path.isdir(ISSUE_DIR):
        return issues
    for name in sorted(os.listdir(ISSUE_DIR)):
        try:
            date_str = name[:6]
            issue_dt = datetime.strptime(date_str, "%y%m%d")
            if mon <= issue_dt <= sun + timedelta(days=1):
                issues.append({"folder": name, "date": issue_dt})
        except ValueError:
            pass
    return issues


def generate_report(anchor: datetime = None) -> str:
    mon, sun = get_week_range(anchor)

    with open(STATS_JSON, "r", encoding="utf-8") as f:
        stats = json.load(f)

    daily = stats["daily"]

    # 이번 주 날짜 목록
    week_dates = []
    cur = mon
    while cur <= sun:
        k = korean_date(cur)
        if k in daily:
            week_dates.append((cur, k, daily[k]))
        else:
            week_dates.append((cur, k, None))
        cur += timedelta(days=1)

    # ── 기본 지표 계산 ──────────────────────────────────────
    total_msgs   = sum(d["msgs"]  for _, _, d in week_dates if d)
    active_days  = sum(1          for _, _, d in week_dates if d and d["msgs"] > 0)
    avg_msgs     = round(total_msgs / active_days, 1) if active_days else 0
    all_users    = set()
    for _, _, d in week_dates:
        if d:
            all_users.update(d.get("user_list", []))
    unique_users = len(all_users)

    daily_msgs  = [(dt, k, d["msgs"] if d else 0)  for dt, k, d in week_dates]
    peak_day    = max(daily_msgs, key=lambda x: x[2])
    low_day     = min(daily_msgs, key=lambda x: x[2])

    # 참여 빈도 TOP5
    user_freq = Counter()
    for _, _, d in week_dates:
        if d:
            for u in d.get("user_list", []):
                user_freq[u] += 1
    top5 = user_freq.most_common(5)

    # 이번 주 이슈
    issues = load_issues_this_week(mon, sun)

    # 전주 비교 (있으면)
    prev_mon = mon - timedelta(days=7)
    prev_total = 0
    prev_users = set()
    cur2 = prev_mon
    while cur2 < mon:
        k = korean_date(cur2)
        if k in daily:
            prev_total += daily[k]["msgs"]
            prev_users.update(daily[k].get("user_list", []))
        cur2 += timedelta(days=1)
    prev_unique = len(prev_users)

    msg_delta  = total_msgs - prev_total
    user_delta = unique_users - prev_unique
    msg_arrow  = "▲" if msg_delta >= 0 else "▼"
    usr_arrow  = "▲" if user_delta >= 0 else "▼"

    # 토픽 수집
    topics_all = []
    for _, _, d in week_dates:
        if d:
            topics_all.extend(d.get("topics", []))
    topic_counter = Counter(topics_all)

    # ops_note 수집
    ops_notes = []
    for dt, k, d in week_dates:
        if d and d.get("ops_note"):
            ops_notes.append(f"- {dt.strftime('%m/%d')}({weekday_kr(dt)}) {d['ops_note']}")

    # ── 리포트 작성 ─────────────────────────────────────────
    week_label = f"{mon.strftime('%Y-%m-%d')}~{sun.strftime('%m-%d')}"
    filename   = f"{mon.strftime('%y%m%d')}_주간리포트.md"
    filepath   = os.path.join(REPORT_DIR, filename)

    lines = []
    lines.append(f"# 오카방 주간 리포트 — {mon.strftime('%Y년 %m월 %d일')}주")
    lines.append(f"> 생성: {datetime.today().strftime('%Y-%m-%d %H:%M')} | 기간: {mon.strftime('%m/%d')}({weekday_kr(mon)}) ~ {sun.strftime('%m/%d')}({weekday_kr(sun)})")
    lines.append("")

    # 핵심 지표
    lines.append("## 핵심 지표")
    lines.append("")
    lines.append(f"| 지표 | 이번주 | 전주 대비 |")
    lines.append(f"|------|--------|----------|")
    lines.append(f"| 총 메시지 | **{total_msgs}개** | {msg_arrow} {abs(msg_delta)} |")
    lines.append(f"| 참여 인원 | **{unique_users}명** | {usr_arrow} {abs(user_delta)} |")
    lines.append(f"| 활성 일수 | {active_days}일 / 7일 | — |")
    lines.append(f"| 일평균 메시지 | {avg_msgs}개 | — |")
    lines.append(f"| 최다 대화일 | {peak_day[0].strftime('%m/%d')}({weekday_kr(peak_day[0])}) {peak_day[2]}개 | — |")
    lines.append(f"| 최저 대화일 | {low_day[0].strftime('%m/%d')}({weekday_kr(low_day[0])}) {low_day[2]}개 | — |")
    lines.append("")

    # 일별 현황
    lines.append("## 일별 현황")
    lines.append("")
    lines.append("| 날짜 | 메시지 | 참여자 | 바 |")
    lines.append("|------|--------|--------|----|")
    max_msg = max((d["msgs"] for _, _, d in week_dates if d), default=1)
    for dt, k, d in week_dates:
        if d:
            bar_len = round(d["msgs"] / max_msg * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            users_str = str(d["users"])
            flag = f" ⚠️ {d['issue_flag']}" if d.get("issue_flag") else ""
            lines.append(f"| {dt.strftime('%m/%d')}({weekday_kr(dt)}) | {d['msgs']}개 | {users_str}명 | `{bar}`{flag} |")
        else:
            lines.append(f"| {dt.strftime('%m/%d')}({weekday_kr(dt)}) | — | — | `░░░░░░░░░░░░░░░░░░░░` |")
    lines.append("")

    # TOP5 참여자
    lines.append("## 주간 참여자 TOP 5")
    lines.append("")
    lines.append("| 순위 | 닉네임 | 참여일수 |")
    lines.append("|------|--------|---------|")
    for i, (nick, days) in enumerate(top5, 1):
        lines.append(f"| {i} | {nick} | {days}일 |")
    lines.append("")

    # 토픽
    if topic_counter:
        lines.append("## 이번 주 주요 토픽")
        lines.append("")
        for topic, cnt in topic_counter.most_common(8):
            lines.append(f"- {topic} ({cnt}회)")
        lines.append("")

    # 이슈
    lines.append("## 이슈")
    lines.append("")
    if issues:
        for iss in issues:
            lines.append(f"- ⚠️ [{iss['folder']}](../이슈/{iss['folder']}/)")
    else:
        lines.append("- 이번 주 특이 이슈 없음 🟢")
    lines.append("")

    # 운영 메모
    if ops_notes:
        lines.append("## 운영 메모 (일별)")
        lines.append("")
        lines.extend(ops_notes)
        lines.append("")

    # 운영 제안
    lines.append("## 다음 주 운영 제안")
    lines.append("")
    if avg_msgs < 100:
        lines.append("- ⚡ 일평균 메시지가 낮음 → 질문형 대화 유도 콘텐츠 1회 이상 권장")
    if unique_users < 6:
        lines.append("- ⚡ 참여 인원 부족 → 현지인 릴레이 이벤트 or 주말 취향 질문 시도")
    if peak_day[0].weekday() >= 5:
        lines.append("- 📌 주말 대화량이 높음 → 주말 저녁 타겟 콘텐츠 효과적")
    if avg_msgs >= 150:
        lines.append("- ✅ 활성도 양호 → 현재 운영 흐름 유지")
    if not issues:
        lines.append("- ✅ 이슈 없음 → 안정적 운영 중")
    lines.append("")
    lines.append("---")
    lines.append(f"*자동생성: weekly_report.py | {datetime.today().strftime('%Y-%m-%d')}*")

    report = "\n".join(lines)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    return filepath, report


if __name__ == "__main__":
    anchor = None
    if len(sys.argv) > 1:
        try:
            anchor = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        except ValueError:
            print("날짜 형식 오류. 예: python3 weekly_report.py 2026-05-12")
            sys.exit(1)

    filepath, report = generate_report(anchor)
    print(report)
    print(f"\n✅ 리포트 저장: {filepath}")
