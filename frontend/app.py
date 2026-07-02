"""社交匹配系统 - Streamlit前端."""

import streamlit as st
import httpx
import json
import uuid

API_BASE = "http://localhost:8001"

st.set_page_config(
    page_title="社交匹配系统",
    page_icon="🤝",
    layout="wide"
)

st.title("🤝 社交匹配系统")
st.markdown("和AI聊聊天，帮你找到志同道合的伙伴！")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "profile" not in st.session_state:
    st.session_state.profile = None
if "matches" not in st.session_state:
    st.session_state.matches = None
if "collected" not in st.session_state:
    st.session_state.collected = False
if "_init_sent" not in st.session_state:
    st.session_state._init_sent = False


def get_session_id():
    """Get or create session ID."""
    if not st.session_state.session_id:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    return st.session_state.session_id


def send_message(user_input: str):
    """Send message to backend chat API."""
    session_id = get_session_id()
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{API_BASE}/api/chat",
                json={"session_id": session_id, "message": user_input}
            )
            resp.raise_for_status()
            data = resp.json()
        return data
    except httpx.TimeoutException:
        return {"error": "请求超时，请稍后重试"}
    except Exception as e:
        return {"error": f"连接失败: {str(e)}"}


def run_match():
    """Run matching — 返回所有高于阈值的匹配."""
    session_id = get_session_id()
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{API_BASE}/api/match",
                json={"session_id": session_id, "limit": 5}
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": str(e)}


def run_icebreaker(match_idx: int = 0):
    """Run icebreaker for a match."""
    session_id = get_session_id()
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{API_BASE}/api/icebreaker",
                json={"session_id": session_id, "limit": 1}
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": str(e)}


# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    # Chat area
    st.subheader("💬 和AI聊聊")
    st.info("像朋友一样聊聊天，我会慢慢了解你的喜好，然后帮你找到合适的伙伴！")

    # 如果还没有对话，显示固定的开场问题
    if not st.session_state.messages and not st.session_state._init_sent:
        st.session_state._init_sent = True
        init_msg = "嗨！欢迎来社交匹配系统~😊 先随便聊聊吧，你平时有什么兴趣爱好呀？"
        st.session_state.messages.append({"role": "assistant", "content": init_msg})

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User input
    if prompt := st.chat_input("说点什么..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner("AI正在思考..."):
                result = send_message(prompt)

            if "error" in result:
                st.error(result["error"])
            else:
                st.write(result["reply"])
                st.session_state.messages.append({"role": "assistant", "content": result["reply"]})

                if result.get("profile"):
                    st.session_state.profile = result["profile"]
                if result.get("is_complete"):
                    st.session_state.collected = True
                    st.success("✨ 画像采集完成！可以去匹配页面看看推荐了～")

with col2:
    # Profile panel
    st.subheader("📋 你的画像")

    if st.session_state.profile:
        p = st.session_state.profile
        if p.get("name"):
            st.write(f"**姓名:** {p['name']}")
        if p.get("age"):
            st.write(f"**年龄:** {p['age']}")
        if p.get("gender"):
            st.write(f"**性别:** {p['gender']}")
        if p.get("interests"):
            st.write(f"**兴趣:** {', '.join(p['interests'])}")
        if p.get("personality_traits"):
            st.write(f"**性格:** {', '.join(p['personality_traits'])}")
        if p.get("goals"):
            st.write(f"**目标:** {', '.join(p['goals'])}")

        # Progress indicator
        filled = sum(1 for v in [p.get("name"), p.get("age"), p.get("gender"),
                                  p.get("interests"), p.get("personality_traits")]
                     if v and (isinstance(v, str) and v or isinstance(v, list) and v))
        st.progress(filled / 5)
    else:
        st.info("还没开始聊天呢，快去左边和AI聊聊吧～")

    st.markdown("---")

    # Match button
    if st.session_state.collected or st.session_state.profile:
        if st.button("🎯 开始匹配", use_container_width=True):
            with st.spinner("正在匹配中..."):
                match_result = run_match()

            if "error" in match_result:
                st.error(match_result["error"])
            else:
                st.session_state.matches = match_result
                st.success(f"找到 {match_result.get('count', 0)} 个匹配！")

    # Display matches
    if st.session_state.matches:
        st.markdown("---")
        st.subheader("👥 推荐匹配")
        matches = st.session_state.matches.get("matches", [])

        for i, match in enumerate(matches[:5]):  # 最多显示5个
            with st.expander(f"🏆 {match['candidate_name']} (匹配度 {match['score']:.0%})", expanded=(i == 0)):
                # 候选人完整信息
                info_parts = []
                if match.get('gender'):
                    info_parts.append(f"{match['gender']}")
                if match.get('age'):
                    info_parts.append(f"{match['age']}岁")
                if info_parts:
                    st.write(f"**{' · '.join(info_parts)}**")

                if match.get('interests'):
                    st.write(f"**兴趣:** {', '.join(match['interests'])}")
                if match.get('personality_traits'):
                    st.write(f"**性格:** {', '.join(match['personality_traits'])}")
                if match.get('goals'):
                    st.write(f"**目标:** {', '.join(match['goals'])}")

                st.write(f"**共同点:** {', '.join(match.get('common_interests', [])) or '暂无'}")
                for reason in match.get("reasons", []):
                    st.write(f"- {reason}")

                # Icebreaker button for each match
                if st.button(f"💬 生成破冰话术", key=f"ib_{i}", use_container_width=True):
                    with st.spinner("生成中..."):
                        ib_result = run_icebreaker(i)
                    if "error" in ib_result:
                        st.error(ib_result["error"])
                    else:
                        ib = ib_result.get("icebreaker", {})
                        # 直接显示破冰话术，不重复LLM解释文本
                        for s in ib.get("suggestions", []):
                            tone_label = {"casual": "😊 轻松", "professional": "🤝 正式", "humorous": "😂 幽默"}.get(s.get("tone"), s.get("tone"))
                            st.markdown(f"**{tone_label}**：{s.get('text')}")
                            st.caption(s.get("reason", ""))
                        if ib.get("topics"):
                            st.write("**💡 建议话题:**")
                            for t in ib["topics"]:
                                st.write(f"- {t}")

    # Reset button
    st.markdown("---")
    if st.button("🔄 重新开始", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.session_state.profile = None
        st.session_state.matches = None
        st.session_state.collected = False
        st.session_state._init_sent = False
        st.rerun()

# Footer
st.markdown("---")
st.caption("多智能体对话式社交匹配系统 · 基于 Agnes 2.0 Flash")
