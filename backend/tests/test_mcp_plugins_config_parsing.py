import pytest
from fastapi import HTTPException

from app.services.mcp_config_parser import build_plugin_data, extract_servers_from_config


def test_extract_servers_from_mcp_servers():
    source, servers = extract_servers_from_config(
        {
            "mcpServers": {
                "exa": {"type": "http", "url": "https://mcp.example.com"}
            }
        }
    )

    assert source == "mcpServers"
    assert "exa" in servers


def test_extract_servers_from_skills():
    source, servers = extract_servers_from_config(
        {
            "skills": {
                "exa_search": {"type": "streamable_http", "url": "https://mcp.example.com"}
            }
        }
    )

    assert source == "skills"
    assert "exa_search" in servers


def test_extract_single_skill_with_name():
    source, servers = extract_servers_from_config(
        {
            "skill": {
                "name": "exa_search",
                "type": "http",
                "url": "https://mcp.example.com"
            }
        }
    )

    assert source == "skill"
    assert list(servers.keys()) == ["exa_search"]
    assert "name" not in servers["exa_search"]


def test_extract_single_skill_requires_name():
    with pytest.raises(HTTPException) as exc_info:
        extract_servers_from_config(
            {
                "skill": {
                    "type": "http",
                    "url": "https://mcp.example.com"
                }
            }
        )

    assert exc_info.value.status_code == 400
    assert "name" in str(exc_info.value.detail)


def test_build_plugin_data_http_with_server_url_alias():
    plugin_data = build_plugin_data(
        plugin_name="exa_search",
        server_config={"serverUrl": "https://mcp.example.com", "type": "http"},
        enabled=True,
        category="search"
    )

    assert plugin_data["plugin_type"] == "http"
    assert plugin_data["server_url"] == "https://mcp.example.com"
    assert plugin_data["headers"] == {}


def test_build_plugin_data_stdio_requires_command():
    with pytest.raises(HTTPException) as exc_info:
        build_plugin_data(
            plugin_name="local_tool",
            server_config={"type": "stdio", "args": ["run"]},
            enabled=True,
            category="general"
        )

    assert exc_info.value.status_code == 400
    assert "command" in str(exc_info.value.detail)
