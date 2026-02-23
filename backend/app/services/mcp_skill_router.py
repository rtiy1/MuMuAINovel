"""MCP Skill 路由器。

根据用户输入的任务上下文推断 skill 分类，并对插件做优先级排序与筛选。
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple


@dataclass
class SkillRoutingProfile:
    """Skill 路由画像。"""
    scores: Dict[str, float]
    matched_categories: List[str]
    routing_key: str


class MCPSkillRouter:
    """MCP Skill 分类路由器。"""

    # 分类关键词（中英混合，优先实用）
    CATEGORY_KEYWORDS: Dict[str, Tuple[str, ...]] = {
        "search": (
            "搜索", "查找", "联网", "网页", "web", "search", "google", "bing",
            "资料", "新闻", "百科", "wiki",
        ),
        "analysis": (
            "分析", "总结", "评估", "诊断", "报告", "analyze", "analysis",
            "summarize", "review", "insight",
        ),
        "filesystem": (
            "文件", "目录", "读写", "上传", "下载", "path", "file", "folder",
            "filesystem", "disk",
        ),
        "database": (
            "数据库", "sql", "查询", "表", "字段", "postgres", "mysql", "sqlite",
            "db", "database",
        ),
        "api": (
            "接口", "调用", "请求", "服务", "endpoint", "rest", "api", "http",
            "webhook",
        ),
        "generation": (
            "生成", "创作", "改写", "润色", "扩写", "rewrite", "generate", "draft",
            "compose",
        ),
    }
    GENERAL_CATEGORY = "general"

    def build_routing_key(self, task_context: str) -> str:
        """构造稳定的路由键，用于缓存分桶。"""
        profile = self.build_profile(task_context)
        return profile.routing_key

    def build_profile(self, task_context: str) -> SkillRoutingProfile:
        """构建任务上下文的 skill 路由画像。"""
        normalized = (task_context or "").lower()
        scores: Dict[str, float] = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0.0
            for kw in keywords:
                if kw in normalized:
                    score += 1.0
            if score > 0:
                scores[category] = score

        matched_categories = [
            cat for cat, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)
        ]

        if not matched_categories:
            return SkillRoutingProfile(
                scores={},
                matched_categories=[],
                routing_key="all",
            )

        # 取前 2 个分类作为缓存键，兼顾命中率和区分度
        routing_key = "|".join(matched_categories[:2])
        return SkillRoutingProfile(
            scores=scores,
            matched_categories=matched_categories,
            routing_key=routing_key,
        )

    def route_plugins(self, plugins: Sequence[Any], task_context: str) -> Tuple[List[Any], SkillRoutingProfile]:
        """
        根据任务上下文对插件进行排序和筛选。

        策略：
        - 无明显意图：保持原顺序（仅做稳定排序），返回全部插件。
        - 有明显意图：优先匹配分类，保留 general 作为兜底。
        """
        profile = self.build_profile(task_context)
        ranked = self._rank_plugins(list(plugins), profile)

        if not profile.matched_categories:
            return ranked, profile

        matched = set(profile.matched_categories)
        selected = [
            plugin for plugin in ranked
            if self._normalize_category(getattr(plugin, "category", None)) in matched
            or self._normalize_category(getattr(plugin, "category", None)) == self.GENERAL_CATEGORY
        ]

        if not selected:
            return ranked, profile

        return selected, profile

    def _rank_plugins(self, plugins: List[Any], profile: SkillRoutingProfile) -> List[Any]:
        def plugin_score(plugin: Any) -> float:
            category = self._normalize_category(getattr(plugin, "category", None))
            score = profile.scores.get(category, 0.0)
            if category == self.GENERAL_CATEGORY:
                score += 0.2
            return score

        return sorted(
            plugins,
            key=lambda p: (
                -plugin_score(p),
                getattr(p, "sort_order", 0),
                str(getattr(p, "created_at", "")),
            ),
        )

    @staticmethod
    def _normalize_category(category: Any) -> str:
        if isinstance(category, str) and category.strip():
            return category.strip().lower()
        return "general"


mcp_skill_router = MCPSkillRouter()
