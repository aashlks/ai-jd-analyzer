"""Command-line entry point for the general-purpose JD analyzer."""

import json
import os
import sys

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIResponseValidationError,
    APIStatusError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)
from pydantic import ValidationError

from analyzer import analyze_jd


def use_utf8_on_windows() -> None:
    """Keep Chinese prompts and JSON readable in Windows terminals and pipes."""

    if sys.platform != "win32":
        return

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def read_jd() -> str:
    """Read a multi-line JD until the user enters END on its own line."""

    print(
        "请粘贴招聘 JD。粘贴完成后，另起一行输入 END 并按回车：",
        file=sys.stderr,
    )
    lines: list[str] = []

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line.strip().upper() == "END":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def main() -> int:
    """Load configuration, read a JD, call the LLM, and print JSON."""

    use_utf8_on_windows()
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key or api_key == "your_deepseek_api_key_here":
        print(
            "错误：没有找到可用的 DEEPSEEK_API_KEY。请先复制 .env.example 为 .env，"
            "再填入自己的 DeepSeek API Key。",
            file=sys.stderr,
        )
        return 1

    try:
        jd_text = read_jd()
    except KeyboardInterrupt:
        print("\n已取消输入。", file=sys.stderr)
        return 130

    if not jd_text:
        print("错误：JD 内容不能为空。", file=sys.stderr)
        return 1

    print("\n正在调用 LLM 分析，请稍候……", file=sys.stderr)

    try:
        result = analyze_jd(jd_text)
    except AuthenticationError:
        print("错误：DeepSeek API Key 无效，请检查 .env 中的配置。", file=sys.stderr)
        return 1
    except RateLimitError:
        print("错误：DeepSeek 请求过于频繁，请稍后重试。", file=sys.stderr)
        return 1
    except APIConnectionError:
        print("错误：无法连接到 DeepSeek API，请检查网络后重试。", file=sys.stderr)
        return 1
    except APIStatusError as error:
        if error.status_code == 402:
            suggestion = "DeepSeek 账户余额不足，请充值后重试。"
        elif 400 <= error.status_code < 500:
            suggestion = "请检查 DEEPSEEK_MODEL、请求参数和模型使用权限。"
        else:
            suggestion = "服务可能暂时异常，请稍后重试。"
        print(
            f"错误：DeepSeek API 返回了 HTTP {error.status_code}。{suggestion}",
            file=sys.stderr,
        )
        return 1
    except (APIResponseValidationError, ValidationError, ValueError):
        print("错误：模型返回的数据无法通过结构校验，请重新尝试。", file=sys.stderr)
        return 1
    except OpenAIError:
        print("错误：调用 DeepSeek API 时发生异常，请稍后重试。", file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1

    # model_dump() 变成 Python 字典，json.dumps() 再把它格式化为 JSON 文本。
    output = json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
