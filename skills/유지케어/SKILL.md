---
name: 유지케어
description: >
  유지현의 퍼스널 OS(yuji) 전반을 케어하는 오케스트레이터 스킬.
  사업(놀생·테이스트트립·오카방), 개인(교통사고·인맥·FNB마케터) 전 영역에 걸쳐
  할일 정리, 이슈 감지, 대시보드 업데이트, 정부지원 체크, SNS 콘텐츠 생성 등을 처리한다.
triggers:
  - "유지 케어"
  - "퍼스널 OS"
  - "대시보드 업데이트"
  - "오늘 뭐 해야 해"
  - "이번 주 정리"
  - "사이트 배포"
  - "정부지원 뭐 있어"
  - "SNS 콘텐츠 만들어줘"
  - "yuji os"
  - "하네스 업그레이드"
---

# 유지케어 스킬

유지현의 하루/주간/월간 사업·개인 운영을 AI가 함께 케어하는 오케스트레이터.

---

## 담당 에이전트 팀

| 에이전트 | 역할 |
|---|---|
| 유지-오케스트레이터 | 요청 해석 → 에이전트 분배 → 최종 리포트 |
| 유지-개발자 | yuji OS 업데이트·배포 (GitHub push → Vercel) |
| 유지-디자이너 | 화면 구조·디자인 방향 결정, 구현은 개발자에게 위임 |
| 유지-기획자 | 예창 사업계획서, 정부지원 탐색, TasteTrip PRD |
| (위임) 오카방 오케스트레이터 | 오카방 관련 요청 전담 |

---

## Phase 1: 요청 분류

```
A. 사업 — 테이스트트립 (개발, 마케팅, 정부지원)
B. 사업 — 오카방 (운영, 이슈, 이벤트, 공지) → 오카방 오케스트레이터 위임
C. 사업 — SNS/콘텐츠 (놀생, 테이스트트립 SNS)
D. 개인 — 교통사고 (기록 확인, 병원 일정)
E. 개인 — 인맥 (추가, 검색, 관리)
F. 개인 — FNB마케터 (이력서, 자소서, SNS)
G. OS — 대시보드 업데이트 (yuji 사이트 배포)
H. 종합 — 오늘/이번 주 리포트
```

---

## Phase 2: 에이전트별 실행

### G. 대시보드 업데이트 (가장 자주 쓰임)

#### 파일 경로 (⚠️ 공백 있음 — 따옴표 필수)
```
/mnt/c/Users/ryu53/Downloads/yuji os/깃허브/okaband-dashboard/index.html
/mnt/c/Users/ryu53/Downloads/yuji os/깃허브/okaband-dashboard/data.json
```

#### 배포 명령
```bash
cd "/mnt/c/Users/ryu53/Downloads/yuji os/깃허브/okaband-dashboard"
git config user.email "sot.tastetrip@gmail.com" && git config user.name "닭국밥"
git add index.html                       # data.json 수정 시 같이 추가
TOKEN=$(cat ~/.gh_token | tr -d '\n')
git remote set-url origin "https://yuji-boop:${TOKEN}@github.com/yuji-boop/yuji.git"
git commit -m "feat/fix/design: [내용]"
git push origin main
# → yuji-seven.vercel.app 자동 배포 (~30초)
```

⚠️ `git add -A` 금지 — 토큰 등 민감 파일 노출 위험

#### 확정 디자인 원칙 (변경 금지)
- 색상: 흰 / 검정 / 살구(#FF6B35) 3색. warm tone 금지
- 폰트: Pretendard CDN, antialiased
- 아이콘: Lucide 포함 전부 제거 — 텍스트 기호만 (+, ×, ←, ‹, ›)
- 이모지: GNB/UI 금지, 응원 멘트만 허용
- GNB: 90px, 텍스트 15px bold 정중앙, 활성=파랑(#0047AB)
- GNB 레이블: 홈 / 사업 / 카톡방 / 유지
- 스크롤바: `*::-webkit-scrollbar{display:none}` 전역 적용
- 카톡방 대시보드: iframe 없음, index.html 인라인 통합
- data.json: `fetch('data.json?t='+Date.now())`로 로드

### H. 종합 리포트

유지현이 "오늘 뭐 해야 해", "이번 주 정리해줘" 요청 시:

1. 할일 확인 — localStorage 직접 못 읽으므로 유지현에게 현재 상태 확인
2. 테이스트트립 이슈 — 알려진 이슈/TODO
3. 오카방 상태 — 오카방 오케스트레이터 트리거
4. 정부지원 — 마감 임박 체크
5. 리포트 출력

```markdown
## 유지현 데일리 리포트 — [날짜]

### 오늘 당장
- [ ] 항목

### 이번 주 안에
- [ ] 항목

### 이번 달 안에
- [ ] 항목

### 체크 필요
- 항목 (있을 때만)
```

### A. 정부지원 탐색

1. 창업 지원 — 중소벤처기업부, K-스타트업
2. 관광·로컬 분야 — 한국관광공사, 문화체육관광부
3. 여성 창업 — 여성기업종합지원센터
4. 현재 시즌 마감 임박 공고 우선 안내

### C. SNS/콘텐츠

- 플랫폼: 인스타 / 스레드 / 트위터
- 톤: 놀생 = 따뜻한 로컬감성 / 테이스트트립 = 여행+맛집 큐레이션
- 초안 2-3개 제시 → 유지현이 선택 → 복사 가능 형태 출력

---

## Phase 3: 출력 규칙

- 리포트는 복사·붙여넣기 가능한 마크다운
- 유지현이 결정해야 할 것은 선택지로 제시 (결정 강요 금지)
- 오카방 요청은 반드시 오카방 오케스트레이터로 위임 후 결과만 통합
- 응답 간결하게 — 유지현은 짧고 직접적인 소통 선호

---

## 유지현 컨텍스트

| 항목 | 내용 |
|---|---|
| 이름 | 유지현 (닉: 닭국밥) |
| 사업 구조 | 놀생 > 테이스트트립, 현지인맛집/여행 오카방, SNS/콘텐츠 |
| 개인 | 교통사고 치료 중, 인맥 관리, FNB마케터 프리랜서 |
| OS URL | yuji-seven.vercel.app |
| GitHub | yuji-boop/yuji (main 브랜치) |
| 오카방 | 놀생 오픈카톡방 현지인맛집/여행 (~300명대) |
| 이메일 | sot.tastetrip@gmail.com |
| 테이스트트립 라이브 | https://sot-tastetrip.vercel.app/#/places |
| 테이스트트립 데브 | https://dev-sot-tastetrip.vercel.app/#/places |

---

## 유지현 작업 스타일 (AI 대응 기준)

- 말이 짧고 직접적 — "검정으로", "파랑이나?", "너무 크겐 말고" → 바로 적용
- 확정된 스펙은 절대 건드리지 않음 (색상, GNB, 폰트)
- 수정 후 즉시 배포 — 보여주고 판단받는 방식
- "심플이츠베스트" — 기교 없이 데이터가 잘 보이면 됨
- 디자인 의견 있으면 선택지로 물어보고 진행
- data.json 업데이트 시 배포 같이 처리
