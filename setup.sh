#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV="$SCRIPT_DIR/.venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "错误：没有找到 Python 3。请按 README 的 macOS 安装章节操作。" >&2
  exit 1
fi

python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' || {
  echo "错误：需要 Python 3.10 或更高版本。" >&2
  exit 1
}

if [ ! -x "$VENV/bin/python" ]; then
  echo "正在创建虚拟环境……"
  python3 -m venv "$VENV"
fi

if [ ! -f "$SCRIPT_DIR/TTSAPIKEY" ]; then
  cp "$SCRIPT_DIR/TTSAPIKEY.example" "$SCRIPT_DIR/TTSAPIKEY"
  chmod 600 "$SCRIPT_DIR/TTSAPIKEY" 2>/dev/null || true
  echo "已创建 TTSAPIKEY。下一步请填写 API Key 和 VOICE_TYPE。"
fi

echo "安装完成。运行示例："
echo "  $SCRIPT_DIR/tts.sh 文章.md --emotion \"温暖、沉稳地朗读\""
