#!/usr/bin/env python3
"""
Render.com build script: Downloads official exam images from Haydovchi-AI repo.
Runs automatically before the bot starts.
"""
import urllib.request
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).parent
MEDIA_DIR = BASE_DIR / "web" / "media"
DATA_DIR = BASE_DIR / "data"

QUESTIONS_FILE = DATA_DIR / "questions_1200.json"
BASE_CDN = "https://raw.githubusercontent.com/Simon4-ik/Haydovchi-AI/main/public/media/"
QUESTIONS_URL = "https://raw.githubusercontent.com/Simon4-ik/Haydovchi-AI/main/public/data/questions.json"

def download_questions():
    if QUESTIONS_FILE.exists():
        print(f"questions_1200.json already exists ({QUESTIONS_FILE.stat().st_size} bytes), skipping download.")
        return
    print("Downloading official YHQ questions_1200.json...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(QUESTIONS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    with open(QUESTIONS_FILE, "wb") as f:
        f.write(data)
    print(f"Downloaded questions_1200.json ({len(data)} bytes)")

def get_image_names():
    if not QUESTIONS_FILE.exists():
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        bank = json.load(f)
    questions = bank.get("questions", bank) if isinstance(bank, dict) else bank
    img_names = set()
    for q in questions:
        url = q.get("imageUrl") or q.get("image")
        if url:
            fname = url.strip().lstrip("/").replace("media/", "")
            if fname:
                img_names.add(fname)
    return sorted(img_names)

def download_image(fname):
    target = MEDIA_DIR / fname
    if target.exists() and target.stat().st_size > 0:
        return True
    url = BASE_CDN + fname
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
        with open(target, "wb") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"  Failed {fname}: {e}")
        return False

def download_images():
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    img_names = get_image_names()
    missing = [n for n in img_names if not (MEDIA_DIR / n).exists()]
    if not missing:
        print(f"All {len(img_names)} images already present, skipping.")
        return
    print(f"Downloading {len(missing)} missing images (out of {len(img_names)})...")
    with ThreadPoolExecutor(max_workers=20) as exe:
        results = list(exe.map(download_image, missing))
    ok = sum(1 for r in results if r)
    print(f"Downloaded {ok}/{len(missing)} images successfully.")

if __name__ == "__main__":
    download_questions()
    download_images()
    print("Build setup complete!")
