"""匹配决策Agent — 基于向量相似度与规则引擎筛选候选人."""

import math
from backend.utils import cosine_similarity, text_to_vector


# Rule-based scoring weights
WEIGHTS = {
    "interests": 0.30,
    "personality": 0.15,
    "social_preference": 0.10,
    "goal": 0.20,
    "vec_sim": 0.25
}

# Minimum similarity threshold
MIN_SCORE = 0.02

# Age proximity weights — how much age difference affects score
SIGMA_AGE = 5  # Age difference std dev — younger/older within 5 years get bonus


class MatcherAgent:
    """匹配决策Agent，负责候选人筛选与排序."""

    def __init__(self, candidates: list[dict]):
        """
        Args:
            candidates: 候选用户列表，每个元素包含:
                {
                    "user_id": str,
                    "name": str,
                    "profile_json": dict  # 完整画像
                }
        """
        self.candidates = candidates

    def match(self, user_profile: dict, limit: int = 50) -> list[dict]:
        """对用户进行匹配打分和排序.

        Args:
            user_profile: 当前用户的画像数据（含vector）
            limit: 返回结果数量

        Returns:
            匹配结果列表，按分数降序排列
        """
        user_vec = user_profile.get("vector")
        if not user_vec:
            # Fallback: generate vector from profile text
            profile_text = " ".join([
                str(user_profile.get("name") or ""),
                *user_profile.get("interests", []),
                *user_profile.get("personality_traits", []),
                *user_profile.get("goals", [])
            ])
            user_vec = text_to_vector(profile_text)

        results = []
        for candidate in self.candidates:
            cand_profile = candidate.get("profile_json", {})
            cand_vec = cand_profile.get("vector")

            if not cand_vec:
                cand_text = " ".join([
                    cand_profile.get("name", ""),
                    *cand_profile.get("interests", []),
                    *cand_profile.get("personality_traits", []),
                    *cand_profile.get("goals", [])
                ])
                cand_vec = text_to_vector(cand_text)

            # Calculate scores
            vec_sim = cosine_similarity(user_vec, cand_vec) if user_vec and cand_vec else 0.0
            interest_overlap = self._interest_score(user_profile, cand_profile)
            personality_compat = self._personality_score(user_profile, cand_profile)
            goal_match = self._goal_score(user_profile, cand_profile)
            social_score = self._social_preference_score(user_profile, cand_profile)
            age_sim = self._age_score(user_profile, cand_profile)
            gender_same = self._gender_score(user_profile, cand_profile)

            # Weighted composite score
            composite = (
                WEIGHTS["interests"] * interest_overlap +
                WEIGHTS["personality"] * personality_compat +
                WEIGHTS["social_preference"] * social_score +
                WEIGHTS["goal"] * goal_match +
                WEIGHTS["vec_sim"] * vec_sim
            )

            # Age + Gender bonus — both dimension boosts
            age_bonus = age_sim * 0.04
            gender_bonus = gender_same * 0.03

            # Normalize to 0-1
            score = min(1.0, max(0.0, composite + age_bonus + gender_bonus))

            if score >= MIN_SCORE:
                reasons = self._generate_reasons(user_profile, cand_profile, score)
                common = self._find_common(user_profile, cand_profile)
                has_interests = bool(user_profile.get("interests")) or bool(user_profile.get("goals"))
                # 用户画像不全时（没有兴趣/目标），不要求共同点
                # 用户画像完整时，只匹配有共同点的
                if has_interests and not common:
                    continue
                results.append({
                    "candidate_id": candidate["user_id"],
                    "candidate_name": cand_profile.get("name", "匿名用户"),
                    "age": cand_profile.get("age"),
                    "gender": cand_profile.get("gender", "未知"),
                    "interests": cand_profile.get("interests", []),
                    "personality_traits": cand_profile.get("personality_traits", []),
                    "goals": cand_profile.get("goals", []),
                    "score": round(score, 3),
                    "vec_sim": round(vec_sim, 3),
                    "interest_score": round(interest_overlap, 3),
                    "reasons": reasons,
                    "common_interests": common
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    @staticmethod
    def _normalize_interests(interests: list[str]) -> set[str]:
        """标准化兴趣词：去除 踢/打/玩/看 等动词前缀。"""
        raw = set(interests)
        normalized = set()
        action_prefixes = ["踢", "打", "玩", "看", "听", "读", "写", "画", "唱", "跳"]
        for item in interests:
            item = item.strip()
            normalized.add(item)
            for prefix in action_prefixes:
                if item.startswith(prefix) and len(item) > 1:
                    normalized.add(item[len(prefix):])  # 踢足球 → 足球
                    normalized.add(prefix + item[len(prefix):])  # 保留原词
        return normalized

    def _interest_score(self, user: dict, candidate: dict) -> float:
        """计算兴趣重叠度 (Jaccard similarity)，支持近似匹配。"""
        u_ints = self._normalize_interests(user.get("interests", []))
        c_ints = self._normalize_interests(candidate.get("interests", []))
        if not u_ints and not c_ints:
            return 0.5  # Neutral if no data
        if not u_ints or not c_ints:
            return 0.1  # One side missing data — small penalty, not zero
        union = u_ints | c_ints
        return len(u_ints & c_ints) / len(union)

    def _personality_score(self, user: dict, candidate: dict) -> float:
        """计算性格兼容性."""
        u_traits = set(user.get("personality_traits", []))
        c_traits = set(candidate.get("personality_traits", []))
        if not u_traits or not c_traits:
            return 0.3
        # Same traits = compatible, different = complementary
        overlap = len(u_traits & c_traits) / max(len(u_traits), len(c_traits))
        return 0.5 + 0.5 * overlap  # Boost for shared traits

    def _gender_score(self, user: dict, candidate: dict) -> float:
        """计算性别匹配度 — 相同性别或一方未知给中间值，不同性别低分."""
        u_gender = user.get("gender")
        c_gender = candidate.get("gender")
        if not u_gender or not c_gender:
            return 0.5
        return 1.0 if u_gender == c_gender else 0.3

    def _age_score(self, user: dict, candidate: dict) -> float:
        """计算年龄相近度 — 越接近1分越高，差距越大分越低."""
        u_age = user.get("age")
        c_age = candidate.get("age")
        if u_age is None or c_age is None:
            return 0.5  # 无法比较时给中等分
        diff = abs(u_age - c_age)
        # Gaussian: 0岁差=1.0, 5岁差≈0.61, 10岁差≈0.14, 15岁差≈0.01
        return math.exp(-(diff ** 2) / (2 * SIGMA_AGE ** 2))

    def _social_preference_score(self, user: dict, candidate: dict) -> float:
        """计算社交偏好匹配度."""
        u_prefs = set(user.get("social_preferences", []))
        c_prefs = set(candidate.get("social_preferences", []))
        if not u_prefs and not c_prefs:
            return 0.5
        if not u_prefs or not c_prefs:
            return 0.2
        union = u_prefs | c_prefs
        return len(u_prefs & c_prefs) / len(union)

    def _goal_score(self, user: dict, candidate: dict) -> float:
        """计算目标匹配度."""
        u_goals = set(user.get("goals", []))
        c_goals = set(candidate.get("goals", []))
        if not u_goals or not c_goals:
            return 0.2
        intersection = u_goals & c_goals
        if intersection:
            return 0.8 + 0.2 * len(intersection) / max(len(u_goals), len(c_goals))
        return 0.1

    def _generate_reasons(self, user: dict, candidate: dict, score: float) -> list[str]:
        """生成匹配原因."""
        reasons = []
        common_ints = set(user.get("interests", [])) & set(candidate.get("interests", []))
        if common_ints:
            reasons.append(f"共同兴趣：{', '.join(common_ints)}")

        common_goals = set(user.get("goals", [])) & set(candidate.get("goals", []))
        if common_goals:
            reasons.append(f"匹配目标：{', '.join(common_goals)}")

        if score >= 0.7:
            reasons.append("高度匹配！")
        elif score >= 0.4:
            reasons.append("有一定契合度")
        else:
            reasons.append("互补型匹配")

        return reasons

    def _find_common(self, user: dict, candidate: dict) -> list[str]:
        """找出共同点，支持近似匹配（踢足球 ↔ 足球）。"""
        common = []
        u_ints = self._normalize_interests(user.get("interests", []))
        c_ints = self._normalize_interests(candidate.get("interests", []))
        common.extend(u_ints & c_ints)
        u_goals = set(user.get("goals", []))
        c_goals = set(candidate.get("goals", []))
        common.extend(u_goals & c_goals)
        return list(set(common))
