import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from llm_interface.csa_llm_provider import CSAChatClient, load_csa_chat_client


class CSAChatClientTest(unittest.TestCase):
    @patch("llm_interface.csa_llm_provider.urllib.request.urlopen")
    def test_openai_compatible_request_and_usage(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "generated"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        }).encode()
        urlopen.return_value.__enter__.return_value = response
        client = CSAChatClient("https://example.test", "secret", "model")
        answer, usage = client("prompt")
        self.assertEqual(answer, "generated")
        self.assertEqual(usage.total_tokens, 14)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.test/v1/chat/completions")
        self.assertNotIn("secret", request.data.decode())

    def test_loads_metaop_style_config(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "config.json"
            path.write_text(json.dumps({
                "base_url": "https://example.test", "key": "secret", "model": "configured-model"
            }), encoding="utf-8")
            client = load_csa_chat_client(path)
            self.assertEqual(client.model, "configured-model")
            self.assertEqual(client.url, "https://example.test/v1/chat/completions")

    @patch("llm_interface.csa_llm_provider.urllib.request.urlopen")
    def test_lists_available_models_without_exposing_key(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            "data": [{"id": "model-a"}, {"id": "model-b"}]
        }).encode()
        urlopen.return_value.__enter__.return_value = response
        client = CSAChatClient("https://example.test", "secret")
        self.assertEqual(client.list_models(), ["model-a", "model-b"])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.test/v1/models")


if __name__ == "__main__":
    unittest.main()
