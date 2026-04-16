from __future__ import annotations
from langchain_deepseek import ChatDeepSeek
from .settings import ModelSettings, require_env


def make_deepseek_chat(ms: ModelSettings, *, temperature: float = 0.2) -> ChatDeepSeek:
    """统一创建 LangChain 的 DeepSeek Chat 模型。"""
    api_key = require_env(ms.deepseek_api_key_env)
    return ChatDeepSeek(
        model=ms.llm_model,
        temperature=temperature,
        max_tokens=8192,
        api_key=api_key,
    )



