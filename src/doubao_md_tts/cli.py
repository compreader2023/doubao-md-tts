"""豆包 TTS 2.0 异步长文本命令行客户端。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://openspeech.bytedance.com/api/v3/tts"
CONFIG_NAME = "TTSAPIKEY"
MAX_TEXT_LENGTH = 100_000


class TTSConfigError(RuntimeError):
    """配置文件错误。"""


def project_root() -> Path:
    override = os.environ.get("DOUBAO_TTS_HOME")
    if override:
        return Path(override).expanduser().resolve()
    # 可编辑安装时：src/doubao_md_tts/cli.py -> 项目根目录
    candidate = Path(__file__).resolve().parents[2]
    return candidate if (candidate / "pyproject.toml").exists() else Path.cwd()


def config_path(explicit: Path | None = None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    env_path = os.environ.get("DOUBAO_TTS_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return project_root() / CONFIG_NAME


def ensure_config(path: Path) -> None:
    if path.exists():
        return
    template = project_root() / f"{CONFIG_NAME}.example"
    if template.exists():
        shutil.copyfile(template, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
        raise TTSConfigError(
            f"已为你创建配置文件：{path}\n"
            "请先用文本编辑器填写 API Key 和 VOICE_TYPE，然后重新运行。"
        )
    raise TTSConfigError(f"找不到配置文件：{path}")


def load_config(path: Path) -> dict[str, str]:
    ensure_config(path)
    values: dict[str, str] = {}
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise TTSConfigError(
                f"{path} 第 {line_number} 行格式错误，应写成 KEY=VALUE"
            )
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    if not values.get("TTS_API_KEY") and not (
        values.get("APP_ID") and values.get("ACCESS_KEY")
    ):
        raise TTSConfigError(
            f"请编辑 {path}：填写 TTS_API_KEY，或同时填写 APP_ID 和 ACCESS_KEY"
        )
    if not values.get("VOICE_TYPE"):
        raise TTSConfigError(f"请编辑 {path}：填写克隆音色 ID（VOICE_TYPE）")
    return values


def markdown_to_text(markdown: str) -> str:
    """移除常见 Markdown 语法，保留适合朗读的正文和段落。"""
    text = re.sub(r"```[^\n]*\n.*?```", "\n", markdown, flags=re.S)
    text = re.sub(r"~~~[^\n]*\n.*?~~~", "\n", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<https?://[^>]+>", "", text)
    text = re.sub(r"^[ \t]{0,3}#{1,6}[ \t]+", "", text, flags=re.M)
    text = re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M)
    text = re.sub(r"^[ \t]*[-*+][ \t]+", "", text, flags=re.M)
    text = re.sub(r"^[ \t]*\d+[.)、][ \t]+", "", text, flags=re.M)
    text = re.sub(r"[*_~`]", "", text)
    text = re.sub(r"^[ \t]*[-=:| ]{3,}[ \t]*$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise RuntimeError("Markdown 清理后没有可朗读文字")
    if len(text) > MAX_TEXT_LENGTH:
        raise RuntimeError(
            f"正文共 {len(text)} 字符，超过接口单次 {MAX_TEXT_LENGTH} 字符限制"
        )
    return text


def resolve_resource_id(config: dict[str, str], voice_type: str) -> str:
    resource_id = config.get("RESOURCE_ID", "").strip()
    if not resource_id:
        resource_id = "seed-icl-2.0" if voice_type.startswith("S_") else "seed-tts-2.0"
    if voice_type.startswith("S_") and resource_id == "seed-tts-2.0":
        print(
            "提示：S_* 是声音复刻音色，已自动将 RESOURCE_ID 改用 seed-icl-2.0。",
            file=sys.stderr,
        )
        return "seed-icl-2.0"
    return resource_id


def make_headers(
    config: dict[str, str], request_id: str, voice_type: str
) -> dict[str, str]:
    result = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Api-Resource-Id": resolve_resource_id(config, voice_type),
        "X-Api-Request-Id": request_id,
    }
    if config.get("TTS_API_KEY"):
        result["X-Api-Key"] = config["TTS_API_KEY"]
    else:
        result["X-Api-App-Id"] = config["APP_ID"]
        result["X-Api-Access-Key"] = config["ACCESS_KEY"]
    return result


def post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}：{detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"网络请求失败：{exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("服务端返回了无法解析的数据") from exc


def response_data(response: dict) -> dict:
    data = response.get("data")
    return data if isinstance(data, dict) else response


def submit(
    config: dict[str, str], text: str, emotion: str, args: argparse.Namespace
) -> str:
    request_id = str(uuid.uuid4())
    voice_type = args.voice or config["VOICE_TYPE"]
    additions = {"context_texts": [emotion]}
    payload = {
        "user": {"uid": config.get("USER_ID", "md-tts-user")},
        "unique_id": request_id,
        "req_params": {
            "text": text,
            "speaker": voice_type,
            "audio_params": {
                "format": args.format,
                "sample_rate": args.sample_rate,
                "speech_rate": args.speech_rate,
                "loudness_rate": args.loudness_rate,
            },
            "additions": json.dumps(additions, ensure_ascii=False),
        },
    }
    response = post_json(
        f"{BASE_URL}/submit",
        payload,
        make_headers(config, request_id, voice_type),
    )
    data = response_data(response)
    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError("提交任务失败：" + json.dumps(response, ensure_ascii=False))
    return str(task_id)


def poll(
    config: dict[str, str],
    task_id: str,
    voice_type: str,
    interval: int,
    timeout: int,
) -> dict:
    deadline = time.monotonic() + timeout
    while True:
        response = post_json(
            f"{BASE_URL}/query",
            {"task_id": task_id},
            make_headers(config, str(uuid.uuid4()), voice_type),
        )
        data = response_data(response)
        status = data.get("task_status")
        if status == 2 or data.get("audio_url"):
            return data
        if status == 3:
            raise RuntimeError("合成失败：" + json.dumps(response, ensure_ascii=False))
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"等待超过 {timeout} 秒；任务 ID：{task_id}。"
                "稍后可使用 --task-id 继续查询。"
            )
        print(f"任务 {task_id} 合成中，{interval} 秒后再查询……", flush=True)
        time.sleep(interval)


def download(url: str, destination: Path) -> None:
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_suffix(destination.suffix + ".part")
    try:
        with urlopen(url, timeout=180) as response, part.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        part.replace(destination)
    except Exception:
        part.unlink(missing_ok=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将 Markdown 文档通过豆包 TTS 2.0 异步长文本接口转换成音频"
    )
    parser.add_argument("markdown", nargs="?", type=Path, help="要朗读的 .md 文件")
    parser.add_argument("--emotion", "-e", help="整篇文章的中文情绪/演绎指令")
    parser.add_argument("--output", "-o", type=Path, help="输出路径；默认与文档同名")
    parser.add_argument("--voice", help="临时覆盖配置中的 VOICE_TYPE")
    parser.add_argument("--config", type=Path, help="使用指定的配置文件")
    parser.add_argument("--task-id", help="不提交新任务，仅继续查询已有任务")
    parser.add_argument(
        "--format", choices=["mp3", "wav", "ogg_opus", "pcm"], default="mp3"
    )
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--speech-rate", type=int, default=0, help="语速百分比，默认 0")
    parser.add_argument(
        "--loudness-rate", type=int, default=0, help="音量百分比，默认 0"
    )
    parser.add_argument("--interval", type=int, default=10, help="轮询间隔秒数")
    parser.add_argument("--timeout", type=int, default=10800, help="最长等待秒数")
    parser.add_argument("--keep-text", action="store_true", help="保存清理后的文本")
    parser.add_argument(
        "--dry-run", action="store_true", help="只清理并检查文本，不调用 API"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.task_id and not args.markdown:
        raise RuntimeError("请提供 Markdown 文件，或使用 --task-id 查询已有任务")
    if args.markdown and not args.markdown.expanduser().is_file():
        raise RuntimeError(f"找不到 Markdown 文件：{args.markdown}")

    text: str | None = None
    if args.markdown:
        args.markdown = args.markdown.expanduser().resolve()
        text = markdown_to_text(args.markdown.read_text(encoding="utf-8-sig"))
        if args.keep_text or args.dry_run:
            preview = args.markdown.with_suffix(".tts.txt")
            preview.write_text(text, encoding="utf-8")
            print(f"已保存清理后的文本：{preview}")
        if args.dry_run:
            print(f"检查通过：共 {len(text)} 个字符；未调用 API。")
            return 0

    config = load_config(config_path(args.config))
    voice_type = args.voice or config["VOICE_TYPE"]
    if args.task_id:
        task_id = args.task_id
    else:
        emotion = args.emotion or input("请输入整篇文章的中文情绪/演绎指令：").strip()
        if not emotion:
            raise RuntimeError("情绪描述不能为空")
        assert text is not None
        task_id = submit(config, text, emotion, args)
        print(f"任务已提交：{task_id}", flush=True)

    data = poll(config, task_id, voice_type, args.interval, args.timeout)
    audio_url = data.get("audio_url")
    if not audio_url:
        raise RuntimeError(
            "任务成功但没有 audio_url：" + json.dumps(data, ensure_ascii=False)
        )
    if args.output:
        output = args.output
    elif args.markdown:
        output = args.markdown.with_suffix("." + args.format)
    else:
        output = Path.cwd() / f"{task_id}.{args.format}"
    download(audio_url, output)
    output = output.expanduser().resolve()
    metadata = output.with_suffix(output.suffix + ".json")
    metadata.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成：{output}")
    print(f"任务信息：{metadata}")
    return 0


def entrypoint() -> int:
    try:
        return main()
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        return 130
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
