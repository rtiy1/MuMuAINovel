"""Anthropic 客户端"""
import json
from typing import Any, AsyncGenerator, Dict, Optional

from anthropic import AsyncAnthropic

from app.logger import get_logger
from app.services.ai_config import AIClientConfig, default_config

logger = get_logger(__name__)


class AnthropicClient:
    """Anthropic API 客户端"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, config: Optional[AIClientConfig] = None):
        self.config = config or default_config
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncAnthropic(**kwargs)

    @staticmethod
    def _stringify_arguments(arguments: Any) -> str:
        """将工具参数统一为 JSON 字符串，便于与 MCP 调用链对齐。"""
        if isinstance(arguments, str):
            return arguments
        if arguments is None:
            return ""
        try:
            return json.dumps(arguments, ensure_ascii=False)
        except Exception:
            return str(arguments)

    @staticmethod
    def _convert_tools_for_anthropic(tools: list) -> list:
        """
        将 OpenAI Function Calling 工具格式转换为 Anthropic 工具格式。

        支持两种输入：
        1. OpenAI: {"type":"function","function":{"name","description","parameters"}}
        2. Anthropic: {"name","description","input_schema"}
        """
        converted = []
        for tool in tools:
            if not isinstance(tool, dict):
                continue

            # Anthropic 原生格式
            if "name" in tool and "input_schema" in tool:
                converted.append({
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("input_schema") or {"type": "object", "properties": {}},
                })
                continue

            # OpenAI Function Calling 格式
            function = tool.get("function")
            if isinstance(function, dict):
                parameters = function.get("parameters") or {"type": "object", "properties": {}}
                if isinstance(parameters, dict):
                    parameters = {k: v for k, v in parameters.items() if k != "$schema"}
                converted.append({
                    "name": function.get("name", ""),
                    "description": function.get("description", ""),
                    "input_schema": parameters,
                })

        return converted

    @staticmethod
    def _build_tool_choice(tool_choice: Optional[str]) -> Optional[Dict[str, str]]:
        """将通用 tool_choice 映射到 Anthropic 格式。"""
        if tool_choice == "required":
            return {"type": "any"}
        if tool_choice == "auto":
            return {"type": "auto"}
        return None

    async def chat_completion(
        self,
        messages: list,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None,
        tools: Optional[list] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools and tool_choice != "none":
            anthropic_tools = self._convert_tools_for_anthropic(tools)
            if anthropic_tools:
                kwargs["tools"] = anthropic_tools
                choice = self._build_tool_choice(tool_choice)
                if choice:
                    kwargs["tool_choice"] = choice

        response = await self.client.messages.create(**kwargs)

        tool_calls = []
        content = ""
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": self._stringify_arguments(block.input),
                    },
                })
            elif block.type == "text":
                content += block.text

        return {
            "content": content,
            "tool_calls": tool_calls if tool_calls else None,
            "finish_reason": response.stop_reason,
        }

    async def chat_completion_stream(
        self,
        messages: list,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None,
        tools: Optional[list] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成，支持工具调用
        
        Yields:
            Dict with keys:
            - content: str - 文本内容块
            - tool_calls: list - 工具调用列表（如果有）
            - done: bool - 是否结束
        """
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools and tool_choice != "none":
            anthropic_tools = self._convert_tools_for_anthropic(tools)
            if anthropic_tools:
                kwargs["tools"] = anthropic_tools
                choice = self._build_tool_choice(tool_choice)
                if choice:
                    kwargs["tool_choice"] = choice

        try:
            async with self.client.messages.stream(**kwargs) as stream:
                try:
                    # 优先消费文本流，兼容 Anthropic SDK 的事件细节变化
                    async for text in stream.text_stream:
                        if text:
                            yield {"content": text}

                    # 从最终消息中提取工具调用，避免逐事件解析造成兼容问题
                    final_message = await stream.get_final_message()
                    tool_calls = []
                    for block in final_message.content:
                        if block.type == "tool_use":
                            tool_calls.append({
                                "id": block.id,
                                "type": "function",
                                "function": {
                                    "name": block.name,
                                    "arguments": self._stringify_arguments(block.input),
                                },
                            })

                    if tool_calls:
                        yield {"tool_calls": tool_calls}
                    yield {"done": True, "finish_reason": final_message.stop_reason}
                except GeneratorExit:
                    # 生成器被关闭，这是正常的清理过程
                    logger.debug("Anthropic 流式响应生成器被关闭(GeneratorExit)")
                    raise
                except Exception as iter_error:
                    logger.error(f"Anthropic 流式响应迭代出错: {str(iter_error)}")
                    raise
        except GeneratorExit:
            # 重新抛出GeneratorExit，让调用方处理
            raise
        except Exception as e:
            logger.error(f"Anthropic 流式请求出错: {str(e)}")
            raise
