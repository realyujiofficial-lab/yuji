#!/usr/bin/env python3
"""stats.json → okaband-dashboard/data.json 복사 후 git push"""
import os, shutil, subprocess, sys

STATS = "/mnt/c/Users/ryu53/Downloads/깃허브/harness-main/놀생_오픈카톡방/_workspace/stats.json"
DASHBOARD = "/mnt/c/Users/ryu53/Downloads/깃허브/okaband-dashboard"
DATA_OUT = os.path.join(DASHBOARD, "data.json")

if not os.path.exists(STATS):
    print("❌ stats.json 없음. extract_stats.py 먼저 실행하세요.")
    sys.exit(1)

shutil.copy2(STATS, DATA_OUT)
print(f"✅ data.json 복사 완료")

def run(cmd, cwd=DASHBOARD):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [WARN] {' '.join(cmd)}: {r.stderr.strip()}")
    return r.returncode == 0

run(["git", "add", "data.json"])
run(["git", "commit", "-m", "chore: update data.json"])

result = subprocess.run(["git", "push"], cwd=DASHBOARD, capture_output=True, text=True)
if result.returncode == 0:
    print("🚀 Vercel 배포 트리거 완료 (~30초 후 반영)")
else:
    print(f"❌ git push 실패: {result.stderr.strip()}")
    print("   git remote 설정 확인 또는 수동으로 push 하세요.")
