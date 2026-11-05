import urllib.request
import re
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).parent.parent
QUESTIONS_FILE = BASE_DIR / "data" / "questions_1200.json"
GURU_CACHE_FILE = BASE_DIR / "data" / "guru_russian_raw.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_bilet_ru(bilet_num):
    url = f"https://gurupdd.uz/bilet/{bilet_num}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        match = re.search(r'GuruQuiz\.init\(\{.*?questions:\s*(\[.*?\])\s*,\s*title:', html, re.DOTALL)
        if not match:
            match = re.search(r'questions:\s*(\[\{.*?\}\])', html, re.DOTALL)
        if match:
            questions = json.loads(match.group(1))
            return (bilet_num, questions)
    except Exception as e:
        print(f"  [Xato] Bilet {bilet_num} (RU): {e}")
    return (bilet_num, [])

def main():
    print("60 ta bilet rus tilida yuklanmoqda (gurupdd.uz)...")
    start = time.time()
    results = {}

    with ThreadPoolExecutor(max_workers=10) as exe:
        bilet_results = list(exe.map(fetch_bilet_ru, range(1, 61)))

    for bilet_num, q_list in bilet_results:
        results[bilet_num] = q_list

    total_ru = sum(len(q) for q in results.values())
    print(f"Yuklandi: {total_ru} ta savol {time.time() - start:.2f} soniyada.")

    with open(GURU_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Mavjud questions_1200.json bilan birlashtirish
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    current_questions = current_data.get("questions", [])
    print(f"Hozirgi savollar: {len(current_questions)} ta")

    # Har bir bilet bo'yicha savollarni ruscha bilan boyitish
    # current_questions: bilet 1 da 20 ta, bilet 2 da 20 ta...
    merged_count = 0
    for q in current_questions:
        b_num = q.get("biletNumber", 1)
        q_num = q.get("questionNumber", 1)
        
        ru_bilet = results.get(b_num, [])
        if ru_bilet and (q_num - 1) < len(ru_bilet):
            ru_q = ru_bilet[q_num - 1]
            q["text_ru"] = ru_q.get("q", q.get("text_uz", ""))
            q["options_ru"] = ru_q.get("a", q.get("options_uz", []))
            q["explanation_ru"] = ru_q.get("hint", "Ответ выбран согласно ПДД.")
            merged_count += 1
        else:
            # Fallback
            q["text_ru"] = q.get("text_uz", "")
            q["options_ru"] = q.get("options_uz", [])
            q["explanation_ru"] = "Ответ выбран согласно ПДД."

    print(f"Muvaffaqiyatli ruscha matnlar ulandi: {merged_count} / {len(current_questions)}")

    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)

    print("Yangi questions_1200.json to'liq O'zbekcha va Ruscha dual formatda saqlandi!")

if __name__ == "__main__":
    main()
