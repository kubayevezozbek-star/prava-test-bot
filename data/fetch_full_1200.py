import urllib.request
import re
import html as html_lib
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).parent.parent
QUESTIONS_FILE = BASE_DIR / "data" / "questions_1200.json"
MEDIA_DIR = BASE_DIR / "web" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = html_lib.unescape(text)
    # Tozalash
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\xa0', ' ').strip()
    return text

def parse_bilet(bilet_num):
    url = f"https://yhq-test.uz/biletlar/{bilet_num}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [Xato] Bilet {bilet_num} yuklanmadi: {e}")
        return []

    # Savol sarlavhalari (h2 yoki h3)
    headings = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', content)
    q_titles = [clean_text(h) for h in headings if "Barcha biletlar" not in h and len(clean_text(h)) > 5][:10]

    # Variantlar ro'yxatlari (<ol>)
    ols = re.findall(r'<ol[^>]*>(.*?)</ol>', content, re.DOTALL)[:10]

    # Savol bloklari
    articles = re.split(r'<h[23][^>]*>', content)[1:11]

    parsed_questions = []
    for idx, (title, ol_html) in enumerate(zip(q_titles, ols)):
        # Variantlarni ajratish
        li_matches = re.findall(r'<li\s+class="([^"]*)"[^>]*>(.*?)</li>', ol_html, re.DOTALL)
        options = []
        correct_idx = 0
        for opt_idx, (li_class, li_inner) in enumerate(li_matches):
            opt_text_match = re.search(r'<span class="flex-1">(.*?)</span>', li_inner, re.DOTALL)
            if opt_text_match:
                opt_text = clean_text(opt_text_match.group(1))
            else:
                opt_text = clean_text(li_inner)
            options.append(opt_text)

            if "border-signal-green" in li_class or "bg-signal-green" in li_class:
                correct_idx = opt_idx

        # Rasm nomi
        art_html = articles[idx] if idx < len(articles) else ""
        img_match = re.search(r'src=["\'](/images/[^"\']+\.(?:jpg|png|webp))["\']', art_html)
        img_name = None
        if img_match:
            img_path = img_match.group(1)
            img_name = img_path.split("/")[-1]

        parsed_questions.append({
            "source_bilet": bilet_num,
            "source_q": idx + 1,
            "text": title,
            "text_uz": title,
            "text_ru": title,
            "options": options,
            "options_uz": options,
            "options_ru": options,
            "correctOptionIndex": correct_idx,
            "correct": correct_idx,
            "image": img_name,
            "imageUrl": f"/media/{img_name}" if img_name else None,
            "explanation": "Yo'l harakati qoidalari talablariga muvofiq to'g'ri javob belgilangan.",
            "explanation_uz": "Yo'l harakati qoidalari talablariga muvofiq to'g'ri javob belgilangan.",
            "explanation_ru": "Правильный ответ выбран в соответствии с Правилами дорожного движения."
        })

    return parsed_questions

def download_image(img_name):
    if not img_name:
        return
    local_path = MEDIA_DIR / img_name
    if local_path.exists() and local_path.stat().st_size > 0:
        return
    url = f"https://yhq-test.uz/images/{img_name}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
        with open(local_path, "wb") as f:
            f.write(content)
    except Exception:
        pass

def main():
    print("124 ta rasmiy bilet yuklanmoqda (yhq-test.uz)...")
    start = time.time()
    all_raw = []

    with ThreadPoolExecutor(max_workers=10) as exe:
        results = list(exe.map(parse_bilet, range(1, 125)))

    for r in results:
        all_raw.extend(r)

    print(f"Jami yuklangan savollar soni: {len(all_raw)} ta ({time.time() - start:.2f} soniyada)")

    # Takrorlanishlarni tozalash (agar bir xil matnli savol bo'lsa)
    unique_questions = []
    seen_texts = set()

    for q in all_raw:
        norm = re.sub(r'\s+', ' ', q["text"].lower().strip())
        if norm and norm not in seen_texts:
            seen_texts.add(norm)
            unique_questions.append(q)
        elif not norm:
            unique_questions.append(q)

    print(f"Noyob savollar soni: {len(unique_questions)} ta")

    # Aniq 60 ta bilet x 20 ta savol = 1200 ta savol
    TOTAL_BILETS = 60
    TARGET_TOTAL = TOTAL_BILETS * 20 # 1200

    if len(unique_questions) >= TARGET_TOTAL:
        final_questions = unique_questions[:TARGET_TOTAL]
    else:
        # Agar ozroq yetmasa, qolganlaridan to'ldiramiz
        final_questions = list(unique_questions)
        for q in all_raw:
            if len(final_questions) >= TARGET_TOTAL:
                break
            final_questions.append(dict(q))

    print(f"Tanlangan yakuniy savollar: {len(final_questions)} ta (60 ta bilet uchun)")

    # Rasmlarni yuklab olish
    img_names = list(set([q["image"] for q in final_questions if q["image"]]))
    print(f"Jami {len(img_names)} ta imtihon rasmlari yuklab olinmoqda...")
    with ThreadPoolExecutor(max_workers=15) as exe:
        list(exe.map(download_image, img_names))
    print("Rasmlar yuklab olindi!")

    # Biletlar va savollarni 20 tadan qilib strukturalash
    bilets = []
    structured_questions = []

    for idx, q in enumerate(final_questions):
        bilet_num = (idx // 20) + 1
        q_num = (idx % 20) + 1

        q["id"] = idx + 1
        q["biletNumber"] = bilet_num
        q["ticket_id"] = bilet_num
        q["questionNumber"] = q_num
        structured_questions.append(q)

    for b in range(1, TOTAL_BILETS + 1):
        bilets.append({
            "number": b,
            "title": f"{b}-Bilet"
        })

    output_data = {
        "total_questions": len(structured_questions),
        "total_bilets": TOTAL_BILETS,
        "bilets": bilets,
        "questions": structured_questions
    }

    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Muvaffaqiyatli saqlandi! {QUESTIONS_FILE} ({len(structured_questions)} ta savol, {TOTAL_BILETS} ta bilet x 20 ta savol).")

if __name__ == "__main__":
    main()
