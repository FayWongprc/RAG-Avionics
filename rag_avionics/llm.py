from __future__ import annotations
from langchain_core.messages import HumanMessage, AIMessage
from openai import OpenAI
from .settings import ModelSettings, require_env

#这个文件实现了一个统一的 LLM 调用层，核心思想是：
#用 OpenAI SDK 直接调用所有模型（DeepSeek、智谱、千问都兼容 OpenAI API）
#提供 LangChain 兼容接口，让现有的 LangGraph 工作流无需修改
#支持 非标准参数（如思考模式控制），这是 LangChain 的 ChatOpenAI 做不到的

class LLMWrapper:
    """统一的 LLM 包装器，兼容 LangChain 接口，支持所有非标准参数"""
    
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.2, 
                 extra_body: dict | None = None):
        """
        初始化 LLM 包装器
        Args:
            api_key: API 密钥
            base_url: API 端点
            model: 模型名称
            temperature: 温度参数
            extra_body: 额外的请求体参数（用于非标准参数）
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.extra_body = extra_body
    
    def invoke(self, messages: list):
        """
        LangChain 兼容的 invoke 方法
        
        Args:
            messages: LangChain 格式的消息列表 [HumanMessage(...), ...]
            
        Returns:
            包含 content 属性的响应对象
        """
        # 转换 LangChain 消息格式为 OpenAI 格式
        openai_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, dict):
                openai_messages.append(msg)
        
        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"}  # 强制 JSON 输出
        }
        
        # 添加额外的请求体参数（如果有）
        if self.extra_body:
            request_params["extra_body"] = self.extra_body
        
        # 调用 OpenAI SDK
        response = self.client.chat.completions.create(**request_params)
        
        # 返回 LangChain 兼容的响应对象
        class Response:
            def __init__(self, content):
                self.content = content
        
        return Response(response.choices[0].message.content)


def make_deepseek_chat(ms: ModelSettings, *, temperature: float = 0.2):
    """创建 DeepSeek 模型（不需要额外参数）"""
    api_key = require_env(ms.deepseek_api_key_env)
    return LLMWrapper(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model=ms.deepseek_model,
        temperature=temperature,
        extra_body={"thinking": {"type": "disabled"}}  # 显式关闭思考模式
    )


def make_zhipu_chat(ms: ModelSettings, *, temperature: float = 0.2):
    """创建智谱 GLM 模型（显式关闭思考模式以提升速度）
    
    智谱思考模式参数格式：
    extra_body={"thinking": {"type": "enabled"}}  # 开启
    extra_body={"thinking": {"type": "disabled"}}  # 关闭
    """
    api_key = require_env(ms.zhipu_api_key_env)
    return LLMWrapper(
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        model=ms.zhipu_model,
        temperature=temperature,
        extra_body={"thinking": {"type": "disabled"}}  # 显式关闭思考模式
    )


def make_qwen_chat(ms: ModelSettings, *, temperature: float = 0.2):
    """创建千问模型（显式关闭思考模式以提升速度）
    
    千问思考模式参数格式：
    extra_body={"enable_thinking": True}  # 开启
    extra_body={"enable_thinking": False}  # 关闭
    """
    api_key = require_env(ms.qwen_api_key_env)
    return LLMWrapper(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model=ms.qwen_model,
        temperature=temperature,
        extra_body={"enable_thinking": False}  # 显式关闭思考模式
    )


def make_llm(ms: ModelSettings, *, temperature: float = 0.2):
    """
    根据配置创建 LLM（支持多种模型）
    
    所有模型都使用统一的 OpenAI SDK 接口，确保：
    - 完全控制所有参数（包括非标准参数）
    - 统一的调用方式
    - LangChain 兼容的接口
    """
    if ms.llm_provider == "deepseek":
        return make_deepseek_chat(ms, temperature=temperature)
    elif ms.llm_provider == "zhipu":
        return make_zhipu_chat(ms, temperature=temperature)
    elif ms.llm_provider == "qwen":
        return make_qwen_chat(ms, temperature=temperature)
    else:
        raise ValueError(f"不支持的 LLM 提供商: {ms.llm_provider}")
