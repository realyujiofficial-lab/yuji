## Approach
- Read existing files before writing. Don't re-read unless changed.
- Thorough in reasoning, concise in output.
- Skip files over 100KB unless required.
- No sycophantic openers or closing fluff.
- No emojis or em-dashes.
- Do not guess APIs, versions, flags, commit SHAs, or package names. Verify by reading code or docs before asserting.

---

## 경로 (항상 이 경로 사용)

| 항목 | 경로 |
|---|---|
| 하네스 루트 | `/mnt/c/Users/ryu53/Downloads/yuji os/깃허브/harness-main/` |
| 오카방 데이터 | `놀생_오픈카톡방/` |
| 대화기록 원본 | `놀생_오픈카톡방/대화기록/원본/` |
| stats.json | `놀생_오픈카톡방/_workspace/stats.json` |
| Vercel 레포 | `/mnt/c/Users/ryu53/Downloads/yuji os/깃허브/okaband-dashboard/` |
| data.json | `okaband-dashboard/data.json` |
| 주간리포트 저장 | `놀생_오픈카톡방/운영/주간리포트/` |
| 이슈 폴더 | `놀생_오픈카톡방/운영/이슈/` |

> 경로에 공백(`yuji os`) 포함 — bash 명령 시 반드시 따옴표 처리

---

## 유지현 작업 스타일 (2026-05-18 관찰)

**대화 분석 워크플로우**
1. 카톡 대화 텍스트 복붙 → Claude가 자동 처리
2. `대화기록/원본/YYMMDD_대화기록.txt` 에 내용 추가
3. `_workspace/stats.json` 업데이트 (msgs/users/topics/issue_flag 포함)
4. 이슈 있으면 `운영/이슈/YYMMDD_이슈명/` 폴더 + MD 생성
5. 운영 히스토리 + 전체분석 MD 업데이트
6. 마지막으로 `sync_to_vercel.sh` 실행 → Vercel 반영

**이슈 추적 워크플로우**
- 이슈 발생일: `YYMMDD_이슈명/` — 팩트정리.md + 발언대응기록.md
- 이슈 다음날: `YYMMDD_이슈명N일차/` — 모니터링.md (방 분위기 경과 추적)
- 이탈 없으면 3~5일차 이후 종결 처리

**운영 스타일**
- 확인 질문 최소화, 바로 실행 선호
- 긴 복합 요청도 한 번에 전부 처리
- 분석 결과에 항상 "운영 제안" 포함
- 주간 리포트: 월요일 sync 시 자동 (`weekly_report.py`)

---

## 하네스: 유지케어 (퍼스널 OS)

**목표:** 유지현의 사업·개인 전 영역 케어 — 할일 리포트, 대시보드 배포, SNS 콘텐츠, 정부지원 탐색

**트리거:** "유지 케어", "오늘 뭐 해야 해", "이번 주 정리", "대시보드 업데이트", "정부지원 뭐 있어", "SNS 글 써줘" 시 `유지케어` 스킬을 사용하라.

**에이전트:** `.claude/agents/유지-오케스트레이터.md`
**스킬:** `skills/유지케어/SKILL.md`

**컨텍스트:**
- yuji OS: github.com/yuji-boop/yuji (Vercel 자동 배포)
- 오카방 대시보드: github.com/yuji-boop/yuji (`okaband-dashboard/`)
- 테이스트트립 라이브: https://sot-tastetrip.vercel.app/#/places
- 오카방 관련은 오카방 오케스트레이터로 위임

---

## 하네스: 오카방 운영

**목표:** 놀생 오픈카톡방 운영 전반 자동화 — 로그 분석, 이슈 감지·기록, 멤버 관리, 이벤트 기획, 공지 작성

**트리거:** 오카방 운영 관련 요청(로그 분석, 이슈 기록, 이벤트 기획, 공지 작성, 멤버 관리) 시 `오카방운영` 스킬을 사용하라. 에이전트 팀 구성 또는 하네스 수정 요청 시 `harness` 스킬을 사용하라.

**에이전트 팀:** `.claude/agents/` 참조
- 오케스트레이터 — 전체 조율, 방장 요청 분배
- 로그분석가 — 카카오 로그 파싱, 이탈 패턴, 정보 기여자 추적
- 이슈관리자 — 이슈 사전 감지, 팩트 정리, 파일 자동 생성
- 멤버인텔 — 핵심 기여자 모니터링, 위험 멤버 조기 감지
- 이벤트기획자 — 계절 이벤트, 커버사진, 릴레이, 번개 모임
- 콘텐츠라이터 — 공지 작성, 주간 뉴스, 외부 트렌드 수집

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|---|---|---|---|
| 2026-05-17 | 초기 구성 | 전체 에이전트 팀 | 오카방 운영 자동화 하네스 구축 |
| 2026-05-18 | 경로/작업스타일 추가, 대화분석 워크플로우 명문화 | CLAUDE.md | 실제 작업 패턴 반영 |
