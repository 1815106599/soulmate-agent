"""后端 FastAPI 主应用."""

import sys
import os

# Ensure backend is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.db import init_db, get_or_create_session, update_session, append_conversation, get_conversation_history
from agents import collect_profile, MatcherAgent, generate_icebreaker
from backend.models import (
    ConversationRequest, MatchRequest, AgentResponse, ChatMessage
)
import uuid

# ============================================================
# 全局函数：加载 demo 数据（不依赖 lifespan，确保任何启动方式都能加载）
# ============================================================
def _load_demo_candidates():
    """从 JSON 文件加载 demo 候选用户，包装为 MatcherAgent 需要的格式。"""
    try:
        import json
        demo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "demo_profiles.json"
        )
        with open(demo_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [{"user_id": p["user_id"], "profile_json": p} for p in raw]
    except Exception as e:
        print(f"[SocialMatch] Warning: Could not load demo data: {e}")
        return []


# Demo candidates — 模块加载时立即初始化
DEMO_CANDIDATES = _load_demo_candidates()
print(f"[SocialMatch] DEMO_CANDIDATES loaded: {len(DEMO_CANDIDATES)} candidates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown."""
    # Startup
    init_db()
    print("[SocialMatch] Database initialized.")
    yield
    # Shutdown
    print("[SocialMatch] Shutting down.")


app = FastAPI(
    title="社交匹配系统 API",
    description="多智能体对话式社交匹配系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "社交匹配系统",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /api/chat",
            "match": "POST /api/match",
            "icebreaker": "POST /api/icebreaker",
            "history": "GET /api/history?session_id=xxx",
            "profiles": "GET /api/profiles"
        }
    }


@app.post("/api/chat")
async def chat_endpoint(req: ConversationRequest):
    """对话接口 — 画像采集Agent处理."""
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    # Get current session
    profile = get_or_create_session(session_id)

    # Append user message to history
    conv_history = profile.get("conversation_history", [])
    conv_history.append({"role": "user", "content": req.message})

    # Call collector agent
    try:
        result = await collect_profile(session_id, req.message, conv_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Update profile
    profile["conversation_history"] = conv_history
    profile.update(result["profile"])
    update_session(session_id, profile)

    # Append to conversation table
    append_conversation(session_id, "user", req.message)
    append_conversation(session_id, "assistant", result["reply"])

    return {
        "session_id": session_id,
        "reply": result["reply"],
        "profile": result["profile"],
        "is_complete": result["is_complete"]
    }


@app.post("/api/match")
async def match_endpoint(req: MatchRequest):
    """匹配接口 — 匹配决策Agent处理."""
    session_id = req.session_id
    profile = get_or_create_session(session_id)

    if not profile.get("vector"):
        raise HTTPException(
            status_code=400,
            detail="画像数据不足，请先完成对话采集"
        )

    if not DEMO_CANDIDATES:
        raise HTTPException(
            status_code=503,
            detail="暂无候选用户数据"
        )

    matcher = MatcherAgent(DEMO_CANDIDATES)
    results = matcher.match(profile, limit=req.limit)

    return {
        "session_id": session_id,
        "matches": results,
        "count": len(results)
    }


@app.post("/api/icebreaker")
async def icebreaker_endpoint(req: MatchRequest):
    """破冰接口 — 撮合辅助Agent处理."""
    session_id = req.session_id
    profile = get_or_create_session(session_id)

    # First get matches
    if not DEMO_CANDIDATES:
        raise HTTPException(status_code=503, detail="暂无候选用户数据")

    matcher = MatcherAgent(DEMO_CANDIDATES)
    results = matcher.match(profile, limit=1)

    if not results:
        raise HTTPException(status_code=404, detail="未找到匹配对象")

    top_match = results[0]

    # Generate icebreaker
    try:
        ice_result = await generate_icebreaker(profile, top_match)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Icebreaker error: {str(e)}")

    return {
        "session_id": session_id,
        "matched_candidate": top_match,
        "icebreaker": ice_result
    }


@app.get("/api/history")
async def history_endpoint(session_id: str):
    """获取对话历史."""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    history = get_conversation_history(session_id, limit=50)
    return {
        "session_id": session_id,
        "messages": history
    }


@app.get("/api/profiles")
async def profiles_endpoint():
    """查看所有会话画像（调试用）."""
    # List all sessions from DB
    from sqlalchemy import text
    from backend.db import engine
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT user_id, updated_at FROM user_profiles ORDER BY updated_at DESC")).fetchall()
    return {
        "sessions": [{"user_id": r[0], "updated_at": r[1]} for r in rows]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
