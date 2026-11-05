import json
from aiohttp import web
from pathlib import Path
import database as db
from config import BASE_DIR, QUESTIONS_FILE, TOTAL_TICKETS

routes = web.RouteTableDef()

# Savollar bazasini xotiraga yuklash
with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    RAW_DATA = json.load(f)

if isinstance(RAW_DATA, dict):
    BILETS_DATA = RAW_DATA.get("bilets", [])
    QUESTIONS_DATA = RAW_DATA.get("questions", [])
else:
    QUESTIONS_DATA = RAW_DATA
    b_nums = sorted(list({q.get("biletNumber", q.get("ticket_id", 1)) for q in QUESTIONS_DATA}))
    BILETS_DATA = [{"number": n, "title": f"{n}-Bilet"} for n in b_nums]

for q in QUESTIONS_DATA:
    tid = q.get("biletNumber", q.get("ticket_id", 1))
    q["ticket_id"] = tid
    q["biletNumber"] = tid
    txt = q.get("text", q.get("question", ""))
    q["text"] = txt
    q["question"] = txt
    q["text_uz"] = q.get("text_uz", txt)
    q["text_ru"] = q.get("text_ru", txt)
    opts = q.get("options", [])
    q["options"] = opts
    q["options_uz"] = q.get("options_uz", opts)
    q["options_ru"] = q.get("options_ru", opts)
    exp = q.get("explanation", "")
    q["explanation"] = exp
    q["explanation_uz"] = q.get("explanation_uz", exp)
    q["explanation_ru"] = q.get("explanation_ru", exp)
    c_idx = q.get("correctOptionIndex", q.get("correct", 0))
    q["correctOptionIndex"] = c_idx
    q["correct"] = c_idx
    img = q.get("imageUrl", q.get("image", ""))
    q["imageUrl"] = img
    q["image"] = img

QUESTIONS_BY_ID = {q["id"]: q for q in QUESTIONS_DATA}

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

@routes.get("/")
async def serve_index(request):
    return web.FileResponse(BASE_DIR / "web" / "index.html", headers=NO_CACHE_HEADERS)

@routes.get("/style.css")
async def serve_css(request):
    return web.FileResponse(BASE_DIR / "web" / "style.css", headers=NO_CACHE_HEADERS)

@routes.get("/app.js")
async def serve_js(request):
    return web.FileResponse(BASE_DIR / "web" / "app.js", headers=NO_CACHE_HEADERS)

@routes.get("/health")
@routes.get("/ping")
async def health_check(request):
    return web.Response(text="Prava Test Bot 24/7 faol ishlamoqda!")

@routes.get("/api/user_status")
async def api_user_status(request):
    params = request.query
    user_id = int(params.get("user_id", "0"))
    first_name = params.get("first_name", "Foydalanuvchi")
    username = params.get("username", "")

    if not user_id:
        return web.json_response({"error": "user_id required"}, status=400, headers=NO_CACHE_HEADERS)

    user = await db.get_or_create_user(user_id, first_name, username)
    total_tickets = len(BILETS_DATA) or TOTAL_TICKETS
    access_info = await db.get_user_access(user_id, total_tickets)

    unlocked_list = access_info["unlocked_tickets"]
    max_ticket = max(unlocked_list) if unlocked_list else 3
    if access_info["is_vip"]:
        max_ticket = total_tickets

    return web.json_response({
        "telegram_id": user_id,
        "user_id": user_id,
        "full_name": user.get("full_name"),
        "first_name": user.get("full_name"),
        "username": user.get("username"),
        "is_vip": access_info["is_vip"],
        "vip_until": access_info["vip_until"],
        "has_exam_pass": access_info["has_exam_pass"],
        "exam_pass_until": access_info["exam_pass_until"],
        "exam_attempts": access_info["exam_attempts"],
        "can_take_exam": access_info["can_take_exam"],
        "unlocked_tickets": unlocked_list,
        "unlocked_max_ticket": max_ticket,
        "total_tickets": total_tickets
    }, headers=NO_CACHE_HEADERS)

@routes.post("/api/consume_exam")
async def api_consume_exam(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        if not user_id:
            return web.json_response({"ok": False, "error": "user_id missing"}, status=400)

        success = await db.consume_exam_attempt(user_id)
        return web.json_response({"ok": success}, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=400, headers=NO_CACHE_HEADERS)

@routes.post("/api/select_payment")
async def api_select_payment(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        payment_type = data.get("payment_type", "vip_90")
        details = data.get("details", "")
        ticket_numbers = str(data.get("ticket_numbers", ""))
        amount = int(data.get("amount", 30000))
        if user_id:
            await db.save_pending_selection(user_id, payment_type, details, ticket_numbers, amount)
        return web.json_response({"ok": True}, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=400, headers=NO_CACHE_HEADERS)

@routes.get("/api/questions")
async def api_questions(request):
    return web.json_response(QUESTIONS_DATA, headers=NO_CACHE_HEADERS)

@routes.get("/api/bilets")
async def api_bilets(request):
    return web.json_response(BILETS_DATA, headers=NO_CACHE_HEADERS)

@routes.post("/api/answer")
async def api_answer(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        question_id = int(data.get("question_id"))
        is_correct = bool(data.get("is_correct"))

        if is_correct:
            await db.resolve_user_error(user_id, question_id)
        else:
            await db.save_user_error(user_id, question_id)

        return web.json_response({"status": "ok"}, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400, headers=NO_CACHE_HEADERS)

@routes.get("/api/mistakes")
async def api_mistakes(request):
    user_id = int(request.query.get("user_id", "0"))
    if not user_id:
        return web.json_response([], headers=NO_CACHE_HEADERS)

    mistake_ids = await db.get_user_errors(user_id)
    mistake_questions = [QUESTIONS_BY_ID[qid] for qid in mistake_ids if qid in QUESTIONS_BY_ID]
    return web.json_response(mistake_questions, headers=NO_CACHE_HEADERS)

@routes.post("/api/test_result")
async def api_test_result(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        ticket_id = int(data.get("ticket_id"))
        score = int(data.get("score"))
        total = int(data.get("total", 20))

        await db.record_test_result(user_id, ticket_id, score, total)
        return web.json_response({"status": "ok"}, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400, headers=NO_CACHE_HEADERS)

def create_web_app():
    app = web.Application()
    app.add_routes(routes)
    media_dir = BASE_DIR / "web" / "media"
    if media_dir.exists():
        app.router.add_static("/media", media_dir)
    return app
