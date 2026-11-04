import json
from aiohttp import web
from pathlib import Path
import database as db
from config import BASE_DIR, QUESTIONS_FILE

routes = web.RouteTableDef()

# Load questions once in memory for high speed
with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    QUESTIONS_DATA = json.load(f)

QUESTIONS_BY_ID = {q["id"]: q for q in QUESTIONS_DATA}

@routes.get("/")
async def serve_index(request):
    index_file = BASE_DIR / "web" / "index.html"
    return web.FileResponse(index_file)

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

    user = await db.get_or_create_user(user_id, first_name, username)
    return web.json_response(user)

@routes.get("/api/questions")
async def api_questions(request):
    return web.json_response(QUESTIONS_DATA)

@routes.post("/api/answer")
async def api_answer(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        question_id = int(data.get("question_id"))
        is_correct = bool(data.get("is_correct"))

        if is_correct:
            await db.resolve_mistake(user_id, question_id)
        else:
            await db.record_mistake(user_id, question_id)

        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

@routes.get("/api/mistakes")
async def api_mistakes(request):
    user_id = int(request.query.get("user_id", "0"))
    if not user_id:
        return web.json_response([])

    mistake_ids = await db.get_user_mistakes(user_id)
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
    return app
