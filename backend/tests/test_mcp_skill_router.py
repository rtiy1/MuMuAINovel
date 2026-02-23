from dataclasses import dataclass

from app.services.mcp_skill_router import mcp_skill_router


@dataclass
class DummyPlugin:
    plugin_name: str
    category: str
    sort_order: int = 0
    created_at: str = ""


def test_build_profile_without_match_returns_all_key():
    profile = mcp_skill_router.build_profile("今天天气不错，继续保持专注")

    assert profile.matched_categories == []
    assert profile.routing_key == "all"


def test_build_profile_with_search_and_analysis_keywords():
    profile = mcp_skill_router.build_profile("请联网搜索资料并做分析总结")

    assert "search" in profile.matched_categories
    assert "analysis" in profile.matched_categories
    assert profile.routing_key in {"search|analysis", "analysis|search"}


def test_route_plugins_prefers_matched_with_general_fallback():
    plugins = [
        DummyPlugin(plugin_name="db_tool", category="database", sort_order=2),
        DummyPlugin(plugin_name="search_tool", category="search", sort_order=1),
        DummyPlugin(plugin_name="general_tool", category="general", sort_order=0),
    ]

    routed, profile = mcp_skill_router.route_plugins(plugins, "请帮我搜索最近的新闻")

    assert profile.matched_categories[0] == "search"
    assert [p.plugin_name for p in routed] == ["search_tool", "general_tool"]
