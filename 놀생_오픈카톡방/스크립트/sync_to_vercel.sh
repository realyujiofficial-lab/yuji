#!/bin/bash
# 오카방 stats.json → okaband-dashboard/data.json 동기화 후 GitHub push → Vercel 자동 배포
# 매주 월요일에는 주간 리포트도 자동 생성

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="$(dirname "$SCRIPT_DIR")"
STATS_JSON="$BASE/_workspace/stats.json"
DASHBOARD_DIR="/mnt/c/Users/ryu53/Downloads/yuji os/깃허브/okaband-dashboard"
DATA_JSON="$DASHBOARD_DIR/data.json"

echo "=============================="
echo "  오카방 → Vercel 동기화 시작"
echo "=============================="

# 1. stats.json 존재 확인
if [ ! -f "$STATS_JSON" ]; then
  echo "❌ stats.json 없음: $STATS_JSON"
  exit 1
fi

# 2. 매주 월요일 → 지난주 주간 리포트 자동 생성
DAY_OF_WEEK=$(date +%u)  # 1=월 ~ 7=일
if [ "$DAY_OF_WEEK" = "1" ] || [ "$1" = "--force-report" ]; then
  echo ""
  echo "[0/3] 주간 리포트 생성 (월요일 자동 실행)..."
  python3 "$SCRIPT_DIR/weekly_report.py"
  echo "  ✅ 주간 리포트 저장 완료"
fi

# 3. stats.json → data.json 복사
echo ""
echo "[1/3] data.json 동기화..."
cp "$STATS_JSON" "$DATA_JSON"
echo "  ✅ $DATA_JSON 업데이트 완료"

# 4. git commit & push
echo ""
echo "[2/3] GitHub 커밋 & 푸시..."
cd "$DASHBOARD_DIR"

git add data.json

# 변경사항 있을 때만 커밋
if git diff --cached --quiet; then
  echo "  ℹ️  data.json 변경사항 없음 — 푸시 스킵"
else
  TODAY=$(date +"%Y-%m-%d %H:%M")
  git commit -m "data: 오카방 통계 업데이트 ($TODAY)"
  git push origin main
  echo "  ✅ GitHub 푸시 완료"
fi

echo ""
echo "[3/3] Vercel 자동 배포 트리거됨"
echo "  → https://yuji-seven.vercel.app/ 에서 1~2분 후 반영"
echo ""
echo "=============================="
echo "  완료!"
echo "=============================="
