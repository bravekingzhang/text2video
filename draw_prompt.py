from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import re


# LLM 提供商预设配置
LLM_PROVIDER_PRESETS = {
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-32k",
        "api_key_env": "OPEN_AI_API_KEY",
    },
    "openai": {
        "base_url": None,  # 使用 OpenAI 默认地址
        "default_model": "gpt-4o-mini",
        "api_key_env": "OPEN_AI_API_KEY",
    },
    "minimax": {
        "base_url": "https://api.minimax.io/v1",
        "default_model": "MiniMax-M2.7",
        "api_key_env": "MINIMAX_API_KEY",
        "temperature_range": (0.01, 1.0),  # MiniMax 要求 temperature 在 (0, 1] 范围内
    },
}


def _get_llm_config():
    """获取 LLM 配置，支持多提供商切换。"""
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()

    # 如果设置了 MINIMAX_API_KEY 且没有指定 provider，自动使用 MiniMax
    if not provider and os.getenv("MINIMAX_API_KEY"):
        provider = "minimax"

    # 如果有 provider 预设，使用预设配置
    if provider in LLM_PROVIDER_PRESETS:
        preset = LLM_PROVIDER_PRESETS[provider]
        api_key = os.getenv(preset["api_key_env"])
        if not api_key:
            raise ValueError(f"{preset['api_key_env']} environment variable not set")
        # 使用预设的 base_url，不受 OPEN_AI_BASE_URL 影响
        base_url = preset["base_url"]
        model = os.getenv("LLM_MODEL") or preset["default_model"]
        return {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "provider": provider,
        }

    # 默认行为：使用 OPEN_AI_API_KEY + OPEN_AI_BASE_URL（兼容原有配置）
    api_key = os.getenv("OPEN_AI_API_KEY")
    base_url = os.getenv("OPEN_AI_BASE_URL")
    if not api_key:
        raise ValueError("OPEN_AI_API_KEY environment variable not set")
    model = os.getenv("LLM_MODEL") or "moonshot-v1-32k"
    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "provider": provider or "default",
    }


def _clamp_temperature(temperature, provider):
    """根据提供商约束调整 temperature 参数。"""
    preset = LLM_PROVIDER_PRESETS.get(provider, {})
    temp_range = preset.get("temperature_range")
    if temp_range:
        return max(temp_range[0], min(temp_range[1], temperature))
    return temperature


def _strip_think_tags(text):
    """移除 MiniMax 等模型可能返回的 <think>...</think> 标签内容。"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _extract_json(text):
    """从模型响应中提取 JSON 内容，支持 markdown 代码块包裹。"""
    # 移除 think 标签
    text = _strip_think_tags(text)
    # 移除 markdown 代码块标记
    text = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    text = re.sub(r"\n?```\s*$", "", text.strip())
    return text.strip()


def generate_prompt(user_input):
    # 尝试加载环境变量文件
    load_dotenv('.env', override=True)
    # 尝试加载本地开发环境变量文件
    load_dotenv('.local.env', override=True)

    MIDJOURNEY_PROMPT = '''你好，你是一个可以生成 midjourney 提示词的专家，用户给你一段描述，你来生成对应的提示词!

    请你记住，你要生成的提示词是英文的 ，其格式可能类似于：

    As the sun gently kissed the horizon, casting a warm golden glow across the bustling city streets, a captivating sight unfolded before my eyes. A graceful woman, adorned in an elegant dress that fluttered in the gentle breeze, held a porcelain cup of steaming coffee in her delicate hands.

    ，不要解释用户的任何输入，不需要任何其他废话，我希望你输出的格式是 Json,如下：

    {
    "result":"$prompt"
    }
    '''

    # 获取 LLM 配置
    config = _get_llm_config()

    client = OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )

    temperature = _clamp_temperature(0.3, config["provider"])

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": MIDJOURNEY_PROMPT},
                {"role": "user", "content": user_input},
            ],
            temperature=temperature,
        )
    except Exception as e:
        raise RuntimeError("Failed to create completion: " + str(e))

    try:
        raw_content = completion.choices[0].message.content
        # 提取 JSON（移除 think 标签和 markdown 代码块）
        cleaned = _extract_json(raw_content)
        content = json.loads(cleaned)
        return content['result']
    except (IndexError, KeyError, json.JSONDecodeError):
        raise RuntimeError("Failed to parse completion result")


if __name__ == '__main__':
    user_input = '''你是谁'''
    config = _get_llm_config()
    print(f"Using provider: {config['provider']}, model: {config['model']}")
    print(generate_prompt(user_input))
