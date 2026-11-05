import json
from aiohttp import web
from pathlib import Path
import database as db
from config import BASE_DIR, QUESTIONS_FILE

routes = web.RouteTableDef()

# Savollar bazasini xotiraga yuklash
with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    RAW_DATA = json.load(f)

# Agar format dict (bilets va questions) bo'lsa
if isinstance(RAW_DATA, dict):
    BILETS_DATA = RAW_DATA.get("bilets", [])
    QUESTIONS_DATA = RAW_DATA.get("questions", [])
else:
    QUESTIONS_DATA = RAW_DATA
    # Avtomatik biletlar ro'yxatini shakllantirish
    b_nums = sorted(list({q.get("biletNumber", q.get("ticket_id", 1)) for q in QUESTIONS_DATA}))
    BILETS_DATA = [{"number": n, "title": f"{n}-Bilet"} for n in b_nums]

QUESTIONS_BY_ID = {q["id"]: q for q in QUESTIONS_DATA}

@routes.get("/")
async def serve_index(request):
    return web.FileResponse(BASE_DIR / "web" / "index.html")

@routes.get("/style.css")
async def serve_css(request):
    return web.FileResponse(BASE_DIR / "web" / "style.css")

@routes.get("/app.js")
async def serve_js(request):
    return web.FileResponse(BASE_DIR / "web" / "app.js")

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
        return web.json_response({"error": "user_id required"}, status=400)

    # Foydalanuvchini bazadan olish yoki yaratish
    user = await db.get_or_create_user(user_id, first_name, username)
    
    # Ruxsat etilgan biletlar ro'yxatini yuklash
    total_tickets = len(BILETS_DATA) or 70
    access_info = await db.get_unlocked_tickets(user_id, total_tickets)
    
    return web.json_response({
        "telegram_id": user_id,
        "full_name": user.get("full_name"),
        "username": user.get("username"),
        "is_vip": access_info["is_vip"],
        "vip_until": access_info["vip_until"],
        "unlocked_tickets": access_info["unlocked_tickets"],
        "total_tickets": total_tickets
    })

@routes.get("/api/questions")
async def api_questions(request):
    return web.json_response({
        "bilets": BILETS_DATA,
        "questions": QUESTIONS_DATA
    })

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

        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

@routes.get("/api/mistakes")
async def api_mistakes(request):
    user_id = int(request.query.get("user_id", "0"))
    if not user_id:
        return web.json_response([])

    mistake_ids = await db.get_user_errors(user_id)
    mistake_questions = [QUESTIONS_BY_ID[qid] for qid in mistake_ids if qid in QUESTIONS_BY_ID]
    return web.json_response(mistake_questions)

@routes.post("/api/test_result")
async def api_test_result(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        ticket_id = int(data.get("ticket_id"))
        score = int(data.get("score"))
        total = int(data.get("total", 20))

        await db.record_test_result(user_id, ticket_id, score, total)
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

def create_web_app():
    app = web.Application()
    app.add_routes(routes)
    # Media rasmlarini statik tarqatish
    media_dir = BASE_DIR / "web" / "media"
    if media_dir.exists():
        app.router.add_static("/media", media_dir)
    return app
