#!/usr/bin/env python3
"""
오카방 캡쳐 sync 스크립트
폰에서 upload.html로 업로드한 캡쳐를 가져와 텍스트 추출 후 저장.

실행: python3 sync_from_supabase.py
"""

import os
import json
import urllib.request
import urllib.parse
import base64
import subprocess
from datetime import datetime
from pathlib import Path

# ── 설정 ────────────────────────────────────────────────────────────
SUPABASE_URL = "https://yseynfdirbnlygwpygvp.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY", "")
BUCKET = "okaband-screenshots"

BASE_DIR = Path("/mnt/c/Users/ryu53/Downloads/yuji os/깃허브/harness-main")
LOG_DIR = BASE_DIR / "놀생_오픈카톡방/대화기록/원본"
PROCESSED_FILE = BASE_DIR / ".processed_uploads.json"
PENDING_DIR = BASE_DIR / "놀생_오픈카톡방/대화기록/캡쳐대기"

# ── 처리된 파일 목록 로드 ──────────────────────────────────────────
def load_processed():
    if PROCESSED_FILE.exists():
        return set(json.loads(PROCESSED_FILE.read_text()))
    return set()

def save_processed(processed: set):
    PROCESSED_FILE.write_text(json.dumps(sorted(processed), ensure_ascii=False, indent=2))

# ── Supabase Storage: 파일 목록 조회 ─────────────────────────────
def list_bucket_files():
    payload = json.dumps({"limit": 100, "offset": 0, "sortBy": {"column": "created_at", "order": "asc"}}).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET}",
        data=payload,
        headers={"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

# ── Supabase Storage: 파일 다운로드 ──────────────────────────────
def download_file(path: str) -> bytes:
    req = urllib.request.Request(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}",
        headers={"Authorization": f"Bearer {SUPABASE_KEY}"},
        method="GET"
    )
    with urllib.request.urlopen(req) as r:
        return r.read()

# ── Claude Vision: 이미지에서 카톡 텍스트 추출 ───────────────────
def extract_text_from_image(image_bytes: bytes, filename: str) -> str:
    ext = filename.lower().split('.')[-1]
    media_type_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
    media_type = media_type_map.get(ext, "image/jpeg")

    image_b64 = base64.standard_b64encode(image_bytes).decode()

    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_b64}
                },
                {
                    "type": "text",
                    "text": """이 이미지는 카카오톡 오픈채팅방 대화 캡쳐입니다.
대화 내용을 텍스트로 정확히 추출해주세요.

출력 형식:
[닉네임] [시간] 메시지내용

규칙:
- 날짜 구분선이 있으면 포함: "YYYY년 M월 D일 요일"
- 시스템 메시지(입장/퇴장)도 포함
- 사진/이모티콘은 "(사진)", "(이모티콘)"으로 표시
- 추가 설명 없이 대화 텍스트만 출력"""
                }
            ]
        }]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read().decode())
        return result["content"][0]["text"]

# ── 메인 ─────────────────────────────────────────────────────────
def main():
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    processed = load_processed()

    print("Supabase 버킷 조회 중...")
    try:
        files = list_bucket_files()
    except Exception as e:
        print(f"버킷 조회 실패: {e}")
        return

    new_files = [f for f in files if f.get("name") and f["name"] not in processed]
    if not new_files:
        print("새 파일 없음.")
        return

    print(f"새 파일 {len(new_files)}개 발견.")
    extracted_texts = []

    for f in new_files:
        name = f["name"]
        print(f"  처리 중: {name}")
        try:
            image_bytes = download_file(name)
            text = extract_text_from_image(image_bytes, name)
            extracted_texts.append(text)
            processed.add(name)
            print(f"  추출 완료 ({len(text)}자)")

            # 대기 폴더에도 저장 (검토용)
            ts = datetime.now().strftime("%y%m%d_%H%M%S")
            pending_file = PENDING_DIR / f"{ts}_{name}.txt"
            pending_file.write_text(text, encoding="utf-8")
        except Exception as e:
            print(f"  실패: {e}")

    if not extracted_texts:
        print("추출된 텍스트 없음.")
        return

    # 대화기록 파일에 추가
    today_str = datetime.now().strftime("%y%m%d")
    log_file = LOG_DIR / f"{today_str}_대화기록.txt"
    combined = "\n\n".join(extracted_texts)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n{'='*40}\n[캡쳐 업로드 - {datetime.now().strftime('%Y-%m-%d %H:%M')}]\n{'='*40}\n")
        f.write(combined)
    print(f"\n대화기록 저장: {log_file}")

    save_processed(processed)

    print(f"""
추출 완료. 다음 단계:
1. Claude Code에서 아래 내용을 붙여넣어 stats.json 업데이트:
   "{combined[:200]}..."
2. 또는 대기 폴더 확인: {PENDING_DIR}
""")

if __name__ == "__main__":
    main()
