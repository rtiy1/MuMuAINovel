"""MCP/Skill 配置解析工具。"""
from typing import Any, Dict, Tuple

from fastapi import HTTPException

SUPPORTED_SERVER_TYPES = {"http", "stdio", "streamable_http", "sse"}


def extract_servers_from_config(config: Dict[str, Any]) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """
    从配置中提取服务器定义。

    支持以下根字段：
    - mcpServers: 标准 MCP 配置
    - skills: skill 列表配置
    - skill: 单个 skill 或 skill 映射
    """
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="配置JSON必须是对象")

    for key in ("mcpServers", "skills"):
        if key not in config:
            continue

        servers = config[key]
        if not isinstance(servers, dict):
            raise HTTPException(status_code=400, detail=f"{key} 必须是对象")
        if not servers:
            raise HTTPException(status_code=400, detail=f"{key} 不能为空")
        return key, servers

    if "skill" in config:
        skill_config = config["skill"]
        if not isinstance(skill_config, dict):
            raise HTTPException(status_code=400, detail="skill 必须是对象")
        if not skill_config:
            raise HTTPException(status_code=400, detail="skill 不能为空")

        # 兼容 skill 映射格式：{"skill": {"exa": {...}}}
        if "name" not in skill_config and all(isinstance(v, dict) for v in skill_config.values()):
            return "skill", skill_config

        # 兼容单个 skill 格式：{"skill": {"name": "exa", ...}}
        plugin_name = skill_config.get("name")
        if not isinstance(plugin_name, str) or not plugin_name.strip():
            raise HTTPException(status_code=400, detail="skill 格式必须包含 name 字段")

        normalized_config = dict(skill_config)
        normalized_config.pop("name", None)
        return "skill", {plugin_name.strip(): normalized_config}

    raise HTTPException(
        status_code=400,
        detail="配置JSON必须包含 mcpServers、skills 或 skill 字段"
    )


def build_plugin_data(
    plugin_name: str,
    server_config: Dict[str, Any],
    enabled: bool,
    category: str
) -> Dict[str, Any]:
    """将服务器配置转换为插件数据。"""
    if not isinstance(plugin_name, str) or not plugin_name.strip():
        raise HTTPException(status_code=400, detail="插件名称不能为空")

    if not isinstance(server_config, dict):
        raise HTTPException(status_code=400, detail=f"插件 {plugin_name} 的配置必须是对象")

    # 兼容 skill.server 嵌套结构
    core_config = server_config.get("server")
    if isinstance(core_config, dict):
        parsed_config = core_config
    else:
        parsed_config = server_config

    server_type = parsed_config.get("type") or parsed_config.get("transport") or "http"
    if not isinstance(server_type, str):
        raise HTTPException(status_code=400, detail=f"插件 {plugin_name} 的 type 必须是字符串")
    server_type = server_type.lower()

    if server_type not in SUPPORTED_SERVER_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的服务器类型: {server_type}")

    plugin_data: Dict[str, Any] = {
        "plugin_name": plugin_name.strip(),
        "display_name": plugin_name.strip(),
        "plugin_type": server_type,
        "enabled": enabled,
        "category": category,
        "sort_order": 0
    }

    if server_type in ["http", "streamable_http", "sse"]:
        server_url = (
            parsed_config.get("url")
            or parsed_config.get("server_url")
            or parsed_config.get("serverUrl")
        )
        if not server_url:
            raise HTTPException(status_code=400, detail=f"{server_type}类型插件必须提供url字段")

        headers = parsed_config.get("headers", {})
        if headers is None:
            headers = {}
        if not isinstance(headers, dict):
            raise HTTPException(status_code=400, detail=f"插件 {plugin_name} 的 headers 必须是对象")

        plugin_data["server_url"] = server_url
        plugin_data["headers"] = headers
    elif server_type == "stdio":
        command = parsed_config.get("command")
        if not command:
            raise HTTPException(status_code=400, detail="Stdio类型插件必须提供command字段")

        args = parsed_config.get("args", [])
        if args is None:
            args = []
        if not isinstance(args, list):
            raise HTTPException(status_code=400, detail=f"插件 {plugin_name} 的 args 必须是数组")

        env = parsed_config.get("env", {})
        if env is None:
            env = {}
        if not isinstance(env, dict):
            raise HTTPException(status_code=400, detail=f"插件 {plugin_name} 的 env 必须是对象")

        plugin_data["command"] = command
        plugin_data["args"] = args
        plugin_data["env"] = env

    return plugin_data
