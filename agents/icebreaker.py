"""撮合辅助Agent — 生成个性化破冰话术."""

import httpx
import json
import re
from backend.config import settings


ICEBREAKER_SYSTEM_PROMPT = """你是一个社交破冰助手。你的任务是根据两个用户的画像信息，为他们生成个性化的开场白，降低社交启动成本。

【输入】
- 发起方用户画像：姓名、兴趣、性格、社交偏好
- 匹配对象画像：同上
- 共同点和匹配原因

【输出要求】
1. 生成3条不同风格的破冰话术（casual、professional、humorous）
2. 每条话术不超过2句话，结合双方共同兴趣或特点
3. 给出建议的聊天话题列表（3-5个）
4. 每条话术附带20字内的选用理由

【输出格式】
只输出以下JSON（放在 ```match_output``` 代码块中），不要输出任何JSON之外的文字：
{
  "suggestions": [
    {
      "tone": "casual",
      "text": "破冰话术内容",
      "reason": "简短理由"
    }
  ],
  "topics": ["话题1", "话题2", "话题3"]
}"""


async def generate_icebreaker(user_profile: dict, match_result: dict) -> dict:
    """生成破冰话术.

    Args:
        user_profile: 当前用户画像
        match_result: 匹配结果

    Returns:
        {
            "reply": 助手解释文本,
            "suggestions": 话术建议列表,
            "topics": 建议话题列表
        }
    """
    context = f"""
【发起方用户画像】
- 姓名: {user_profile.get('name', '未提供')}
- 年龄: {user_profile.get('age', '未提供')}
- 兴趣: {', '.join(user_profile.get('interests', [])) or '未提供'}
- 性格: {', '.join(user_profile.get('personality_traits', [])) or '未提供'}
- 目标: {', '.join(user_profile.get('goals', [])) or '未提供'}

【匹配对象画像】
- 姓名: {match_result.get('candidate_name', '未提供')}
- 共同兴趣: {', '.join(match_result.get('common_interests', [])) or '未提供'}
- 匹配原因: {', '.join(match_result.get('reasons', [])) or '未提供'}
"""

    messages = [
        {"role": "system", "content": ICEBREAKER_SYSTEM_PROMPT},
        {"role": "user", "content": context}
    ]

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
                "temperature": settings.icebreaker_temp,
                "max_tokens": 1500,
                "stream": False
            }
        )
        resp.raise_for_status()
        data = resp.json()

    assistant_content = data["choices"][0]["message"]["content"]

    # Extract JSON
    suggestions = []
    topics = []
    match = re.search(r'```match_output\s*\n(.*?)\n```', assistant_content, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            suggestions = parsed.get("suggestions", [])
            topics = parsed.get("topics", [])
        except json.JSONDecodeError:
            pass

    # Clean reply (remove JSON block)
    reply = re.sub(r'\s*```match_output\s*\n.*?\n```', '', assistant_content).strip()

    return {
        "reply": reply,
        "suggestions": suggestions,
        "topics": topics
    }
