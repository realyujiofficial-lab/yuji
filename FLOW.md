# 유지현 OS — 오카방 운영 자동화 흐름

## 전체 구조

```
데이터 입력
├── [방법 A] PC에서 카톡 텍스트 복붙
└── [방법 B] 폰에서 캡쳐 업로드

           ↓

      Claude 처리
      (텍스트 추출 + 분석)

           ↓

   파일 저장 (로컬)
   ├── 대화기록/원본/*.txt
   └── _workspace/stats.json

           ↓

   GitHub Push
   └── okaband-dashboard/data.json 동기화

           ↓

   Vercel 자동 배포
   └── yuji-seven.vercel.app
```

---

## 방법 A — PC에서 직접 입력 (현재 주 방식)

```
1. 카톡 대화 복사
2. Claude Code에 붙여넣기
3. Claude가 자동 처리:
   a. 260517_대화기록.txt 에 원문 추가
   b. _workspace/stats.json 업데이트
      - daily: 날짜별 msgs/users/topics/issue_flag
      - user_stats: 멤버별 누적 메시지 수
   c. okaband-dashboard/data.json 동기화
   d. git push → Vercel 자동 배포
```

---

## 방법 B — 폰에서 캡쳐 업로드 (신규)

```
1. 폰으로 카톡 캡쳐
2. yuji-seven.vercel.app/upload.html 접속
3. 캡쳐 선택 → 업로드
   └── Supabase Storage (okaband-screenshots 버킷)에 저장

[PC 복귀 후]

4. 터미널에서 실행:
   python3 sync_from_supabase.py

5. 스크립트 동작:
   a. Supabase 버킷에서 새 이미지 다운로드
   b. Claude Vision API → 카톡 텍스트 추출
   c. 대화기록/캡쳐대기/*.txt 저장

6. 추출된 텍스트를 Claude Code에 붙여넣기
   → 이후 방법 A와 동일하게 처리
```

---

## 파일 구조

```
harness-main/
├── FLOW.md                          ← 이 파일
├── sync_from_supabase.py            ← 폰 업로드 sync 스크립트
├── 놀생_오픈카톡방/
│   ├── 대화기록/
│   │   ├── 원본/
│   │   │   └── 260517_대화기록.txt  ← 원문 누적
│   │   └── 캡쳐대기/               ← sync 후 검토용 텍스트
│   └── _workspace/
│       └── stats.json              ← 분석 데이터 (원본)
│
okaband-dashboard/
├── data.json                        ← Vercel 배포용 (stats.json 복사본)
├── index.html                       ← 대시보드 메인
├── okaband.html                     ← 오카방 전용 뷰
└── upload.html                      ← 폰 업로드 페이지
```

---

## stats.json 구조

```json
{
  "generated_at": "2026-05-19 13:00",
  "all_dates": ["2026년 02월 17일", ..., "2026년 05월 19일"],
  "daily": {
    "2026년 05월 18일": {
      "msgs": 162,
      "users": 9,
      "user_list": ["닭국밥", "응애", ...],
      "topics": ["실링팬/여름준비", "강원도여행", ...],
      "peak_hours": ["17~19시"],
      "issue_flag": null,
      "ops_note": "신입 온보딩 완료. ...",
      "member_events": { "join": [...], "leave": [...] }
    }
  },
  "user_stats": {
    "전북 군산&서울 송파/로컬여행/닭국밥": { "msgs": 6218, "last": "2026년 05월 19일" }
  }
}
```

---

## 운영 주기

| 주기 | 작업 |
|------|------|
| 매일 | 카톡 대화 복붙 or 캡쳐 업로드 → Claude 처리 |
| 매주 월요일 | 주간 리포트 요청: "이번주 오카방 어때?" |
| 수시 | 이슈 발생 시 Claude에게 상황 설명 → 이슈 파일 자동 생성 |

---

## 주요 URL

| 이름 | URL |
|------|-----|
| 대시보드 | https://yuji-seven.vercel.app |
| 캡쳐 업로드 (폰용) | https://yuji-seven.vercel.app/upload.html |
| GitHub 레포 | https://github.com/yuji-boop/yuji |
