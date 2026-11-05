import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
QUESTIONS_FILE = BASE_DIR / "data" / "questions_1200.json"

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

questions = raw.get("questions", raw) if isinstance(raw, dict) else raw

print(f"Original questions count: {len(questions)}")

# Agar 679 ta bo'lsa, 680-savolni qo'shamiz (34 ta to'liq 20 talik bilet bo'lishi uchun)
if len(questions) == 679:
    q680 = {
        "id": 680,
        "biletNumber": 34,
        "questionNumber": 20,
        "text": "Har qanday yo'l-transport hodisasi sodir bo'lganda haydovchining birinchi navbatdagi majburiyati nima?",
        "text_uz": "Har qanday yo'l-transport hodisasi sodir bo'lganda haydovchining birinchi navbatdagi majburiyati nima?",
        "text_ru": "Какова первоочередная обязанность водителя при любом дорожно-транспортном происшествии?",
        "imageUrl": None,
        "options": [
            "Transport vositasini darhol to'xtatish, avariya ishorasini yoqish va avariya sababli to'xtash belgisini o'rnatish",
            "Hodisa joyidan transport vositasini chetga olib chiqish",
            "Guvohlarni to'plash",
            "Sug'urta kompaniyasiga borish"
        ],
        "options_uz": [
            "Transport vositasini darhol to'xtatish, avariya ishorasini yoqish va avariya sababli to'xtash belgisini o'rnatish",
            "Hodisa joyidan transport vositasini chetga olib chiqish",
            "Guvohlarni to'plash",
            "Sug'urta kompaniyasiga borish"
        ],
        "options_ru": [
            "Немедленно остановить транспортное средство, включить аварийную сигнализацию и выставить знак аварийной остановки",
            "Убрать транспортное средство с места происшествия",
            "Собрать свидетелей",
            "Поехать в страховую компанию"
        ],
        "correctOptionIndex": 0,
        "correct": 0,
        "explanation": "YHQ 2.6-bandi: YTH sodir bo'lganda haydovchi transport vositasini darhol to'xtatishi, avariya ishorasini yoqishi va avariya sababli to'xtash belgisini o'rnatishi, transport vositasini va hodisaga daxldor buyumlarni joyidan qo'zg'atmasligi shart.",
        "explanation_uz": "YHQ 2.6-bandi: YTH sodir bo'lganda haydovchi transport vositasini darhol to'xtatishi, avariya ishorasini yoqishi va avariya sababli to'xtash belgisini o'rnatishi, transport vositasini va hodisaga daxldor buyumlarni joyidan qo'zg'atmasligi shart.",
        "explanation_ru": "Пункт 2.6 ПДД: При ДТП водитель обязан немедленно остановить ТС, включить аварийную сигнализацию, выставить знак аварийной остановки и не перемещать предметы, имеющие отношение к происшествию."
    }
    questions.append(q680)

# Har bir savolga yangi biletNumber (har 20 tadan 1 ta bilet)
new_questions = []
bilets = []
TOTAL_BILETS = 34

for i, q in enumerate(questions):
    bilet_num = (i // 20) + 1
    q_num = (i % 20) + 1
    
    q["id"] = i + 1
    q["biletNumber"] = bilet_num
    q["ticket_id"] = bilet_num
    q["questionNumber"] = q_num
    new_questions.append(q)

for b_num in range(1, TOTAL_BILETS + 1):
    bilets.append({
        "number": b_num,
        "title": f"{b_num}-Bilet"
    })

output_data = {
    "total_questions": len(new_questions),
    "total_bilets": TOTAL_BILETS,
    "bilets": bilets,
    "questions": new_questions
}

with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Successfully reorganized {len(new_questions)} questions into {TOTAL_BILETS} bilets of 20 questions each!")
