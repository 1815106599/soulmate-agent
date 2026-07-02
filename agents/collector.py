"""画像采集Agent — 通过自然对话隐式提取用户画像."""

import httpx
import json
from backend.config import settings
from backend.utils import text_to_vector


COLLECTOR_SYSTEM_PROMPT = """你是一个社交匹配系统的画像采集助手。你的任务是通过自然友好的对话，隐式地了解用户的个人信息、兴趣爱好、性格特点和社交需求。

【核心规则】
1. 不要直接问"你几岁？""你喜欢什么？"这种填表式问题
2. 用聊天的方式引导用户表达，比如分享自己的看法、问开放式问题
3. 每次回复控制在2-4句话，保持对话流畅
4. 不要一次性问太多问题，一次聚焦一个话题
5. 对用户说的话要做出自然回应，像朋友聊天一样
6. 称呼用户时要使用ta告诉你的昵称/姓名，不要自己编一个

【需要采集的信息维度】
- 基本信息：年龄、性别、职业/身份
- 兴趣爱好：运动、音乐、电影、游戏、阅读、美食等
- 性格特征：内向/外向、安静/活泼、理性/感性等
- 社交偏好：喜欢一对一还是群体活动、社交频率、社交场景
- 匹配目标：找运动搭子、学习伙伴、饭友、活动伴侣等

【画像提取】
当用户说了足够多的信息后（至少3轮对话），在回复的最后用以下JSON格式提取画像数据（不要让用户看到JSON，只在内部处理）：

画像数据格式：
{
  "name": "用户昵称或姓名，未知则为null",
  "age": 用户年龄整数，未知则为null,
  "gender": "男/女/其他",
  "interests": ["兴趣1", "兴趣2"],
  "personality_traits": ["性格1", "性格2"],
  "social_preferences": ["偏好1", "偏好2"],
  "goals": ["目标1", "目标2"]
}

注意：JSON必须放在回复内容的最后，用 ```profile_extract``` 包裹。
如果没有足够信息提取某项，该项设为null或空数组。

示例对话流程：
用户："你好"
助手："嗨！欢迎来这里~ 平时有什么兴趣爱好呀？"
```profile_extract
{}
```

用户："我喜欢打篮球和看电影"
助手："哇动静皆宜！我也超爱看电影的，你喜欢什么类型？"
```profile_extract
{"interests": ["篮球", "看电影"]}
```

记住：始终像朋友一样聊天，不要像在审问。用户自称什么名字就用什么名字，绝对不要自己编造或代替。"""


async def collect_profile(session_id: str, user_message: str, conversation_history: list[dict]) -> dict:
    """采集用户画像并生成助手回复.

    Args:
        session_id: 会话ID
        user_message: 用户最新消息
        conversation_history: 历史对话列表

    Returns:
        {
            "reply": 助手回复文本,
            "profile": 提取的画像数据,
            "is_complete": 画像是否已足够完整
        }
    """
    # Build messages for API
    messages = [
        {"role": "system", "content": COLLECTOR_SYSTEM_PROMPT}
    ]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    # Call Agnes AI API
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.agnes_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.agnes_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.agnes_model,
                "messages": messages,
                "temperature": settings.collector_temp,
                "max_tokens": 1024,
                "stream": False
            }
        )
        resp.raise_for_status()
        data = resp.json()

    assistant_content = data["choices"][0]["message"]["content"]

    # Extract profile JSON if present
    profile = _extract_profile(assistant_content)

    # Clean the reply (remove profile extraction block)
    reply = _clean_reply(assistant_content)

    # Determine if profile is complete (enough dimensions filled)
    filled = sum(1 for v in [profile.get("name"), profile.get("age"),
                              profile.get("gender"), profile.get("interests"),
                              profile.get("personality_traits")]
                 if v is not None and v != "")
    is_complete = filled >= 3

    # Generate vector from profile text
    profile_text = " ".join([
        str(profile.get("name") or ""),
        str(profile.get("age") or ""),
        *[str(i) for i in profile.get("interests", []) if i],
        *[str(t) for t in profile.get("personality_traits", []) if t],
        *[str(p) for p in profile.get("social_preferences", []) if p],
        *[str(g) for g in profile.get("goals", []) if g]
    ])
    profile["vector"] = text_to_vector(profile_text, settings.vector_dim)

    return {
        "reply": reply,
        "profile": profile,
        "is_complete": is_complete
    }


def _extract_profile(content: str) -> dict:
    """Extract profile JSON from assistant response."""
    import re
    match = re.search(r'```profile_extract\s*\n(.*?)\n```', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def _clean_reply(content: str) -> str:
    """Remove profile extraction block from response."""
    import re
    return re.sub(r'\s*```profile_extract\s*\n.*?\n```', '', content).strip()
