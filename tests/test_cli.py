import tempfile
import unittest
from pathlib import Path

from doubao_md_tts.cli import (
    TTSConfigError,
    load_config,
    markdown_to_text,
    resolve_resource_id,
)


class MarkdownTests(unittest.TestCase):
    def test_removes_common_markup(self):
        source = "# 标题\n\n这是[链接](https://example.com)。\n\n- 第一项\n\n```py\nprint('x')\n```"
        self.assertEqual(markdown_to_text(source), "标题\n\n这是链接。\n\n第一项")

    def test_empty_document_fails(self):
        with self.assertRaises(RuntimeError):
            markdown_to_text("```py\npass\n```")


class ConfigTests(unittest.TestCase):
    def test_api_key_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TTSAPIKEY"
            path.write_text("TTS_API_KEY=test\nVOICE_TYPE=S_demo\n", encoding="utf-8")
            self.assertEqual(load_config(path)["VOICE_TYPE"], "S_demo")

    def test_missing_credentials_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TTSAPIKEY"
            path.write_text("VOICE_TYPE=S_demo\n", encoding="utf-8")
            with self.assertRaises(TTSConfigError):
                load_config(path)

    def test_clone_resource_auto_detection(self):
        self.assertEqual(resolve_resource_id({}, "S_demo"), "seed-icl-2.0")
        self.assertEqual(
            resolve_resource_id({"RESOURCE_ID": "seed-tts-2.0"}, "S_demo"),
            "seed-icl-2.0",
        )


if __name__ == "__main__":
    unittest.main()
