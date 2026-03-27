"""Unit tests and integration tests for draw_prompt.py multi-provider LLM support."""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from draw_prompt import (
    LLM_PROVIDER_PRESETS,
    _clamp_temperature,
    _extract_json,
    _get_llm_config,
    _strip_think_tags,
    generate_prompt,
)


class TestLLMProviderPresets(unittest.TestCase):
    """Test LLM provider preset configurations."""

    def test_minimax_preset_exists(self):
        self.assertIn("minimax", LLM_PROVIDER_PRESETS)

    def test_minimax_preset_has_correct_base_url(self):
        preset = LLM_PROVIDER_PRESETS["minimax"]
        self.assertEqual(preset["base_url"], "https://api.minimax.io/v1")

    def test_minimax_preset_has_correct_default_model(self):
        preset = LLM_PROVIDER_PRESETS["minimax"]
        self.assertEqual(preset["default_model"], "MiniMax-M2.7")

    def test_minimax_preset_has_correct_api_key_env(self):
        preset = LLM_PROVIDER_PRESETS["minimax"]
        self.assertEqual(preset["api_key_env"], "MINIMAX_API_KEY")

    def test_minimax_preset_has_temperature_range(self):
        preset = LLM_PROVIDER_PRESETS["minimax"]
        self.assertEqual(preset["temperature_range"], (0.01, 1.0))

    def test_moonshot_preset_exists(self):
        self.assertIn("moonshot", LLM_PROVIDER_PRESETS)

    def test_openai_preset_exists(self):
        self.assertIn("openai", LLM_PROVIDER_PRESETS)

    def test_all_presets_have_required_keys(self):
        required_keys = {"base_url", "default_model", "api_key_env"}
        for name, preset in LLM_PROVIDER_PRESETS.items():
            for key in required_keys:
                self.assertIn(key, preset, f"Preset '{name}' missing key '{key}'")


class TestClampTemperature(unittest.TestCase):
    """Test temperature clamping for different providers."""

    def test_minimax_clamps_zero_to_min(self):
        result = _clamp_temperature(0.0, "minimax")
        self.assertAlmostEqual(result, 0.01)

    def test_minimax_keeps_valid_temperature(self):
        result = _clamp_temperature(0.5, "minimax")
        self.assertAlmostEqual(result, 0.5)

    def test_minimax_clamps_high_temperature(self):
        result = _clamp_temperature(1.5, "minimax")
        self.assertAlmostEqual(result, 1.0)

    def test_minimax_preserves_boundary(self):
        result = _clamp_temperature(1.0, "minimax")
        self.assertAlmostEqual(result, 1.0)

    def test_openai_no_clamping(self):
        result = _clamp_temperature(0.0, "openai")
        self.assertAlmostEqual(result, 0.0)

    def test_unknown_provider_no_clamping(self):
        result = _clamp_temperature(2.0, "unknown")
        self.assertAlmostEqual(result, 2.0)

    def test_default_provider_no_clamping(self):
        result = _clamp_temperature(0.3, "default")
        self.assertAlmostEqual(result, 0.3)


class TestStripThinkTags(unittest.TestCase):
    """Test think tag stripping for MiniMax responses."""

    def test_strips_think_tags(self):
        text = '<think>reasoning here</think>{"result": "a prompt"}'
        result = _strip_think_tags(text)
        self.assertEqual(result, '{"result": "a prompt"}')

    def test_strips_multiline_think_tags(self):
        text = '<think>\nlet me think...\nstep 1\nstep 2\n</think>\n{"result": "hello"}'
        result = _strip_think_tags(text)
        self.assertEqual(result, '{"result": "hello"}')

    def test_no_think_tags(self):
        text = '{"result": "a prompt"}'
        result = _strip_think_tags(text)
        self.assertEqual(result, '{"result": "a prompt"}')

    def test_empty_string(self):
        result = _strip_think_tags("")
        self.assertEqual(result, "")

    def test_strips_multiple_think_tags(self):
        text = '<think>a</think>middle<think>b</think>end'
        result = _strip_think_tags(text)
        self.assertEqual(result, "middleend")


class TestExtractJson(unittest.TestCase):
    """Test JSON extraction from model responses."""

    def test_plain_json(self):
        text = '{"result": "a prompt"}'
        result = _extract_json(text)
        self.assertEqual(result, '{"result": "a prompt"}')

    def test_json_in_markdown_code_block(self):
        text = '```json\n{"result": "a prompt"}\n```'
        result = _extract_json(text)
        self.assertEqual(result, '{"result": "a prompt"}')

    def test_json_in_code_block_no_lang(self):
        text = '```\n{"result": "a prompt"}\n```'
        result = _extract_json(text)
        self.assertEqual(result, '{"result": "a prompt"}')

    def test_think_tags_with_code_block(self):
        text = '<think>thinking...</think>```json\n{"result": "hello"}\n```'
        result = _extract_json(text)
        self.assertEqual(result, '{"result": "hello"}')

    def test_think_tags_plain_json(self):
        text = '<think>reasoning</think>{"result": "world"}'
        result = _extract_json(text)
        self.assertEqual(result, '{"result": "world"}')


class TestGetLLMConfig(unittest.TestCase):
    """Test LLM configuration resolution."""

    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax", "MINIMAX_API_KEY": "test-key"}, clear=False)
    def test_minimax_provider_explicit(self):
        config = _get_llm_config()
        self.assertEqual(config["provider"], "minimax")
        self.assertEqual(config["api_key"], "test-key")
        self.assertEqual(config["base_url"], "https://api.minimax.io/v1")
        self.assertEqual(config["model"], "MiniMax-M2.7")

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "auto-key"}, clear=True)
    def test_minimax_auto_detect_via_api_key(self):
        config = _get_llm_config()
        self.assertEqual(config["provider"], "minimax")
        self.assertEqual(config["api_key"], "auto-key")

    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax", "MINIMAX_API_KEY": "k", "LLM_MODEL": "MiniMax-M2.7-highspeed"}, clear=False)
    def test_minimax_custom_model(self):
        config = _get_llm_config()
        self.assertEqual(config["model"], "MiniMax-M2.7-highspeed")

    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax"}, clear=True)
    def test_minimax_missing_key_raises(self):
        with self.assertRaises(ValueError) as ctx:
            _get_llm_config()
        self.assertIn("MINIMAX_API_KEY", str(ctx.exception))

    @patch.dict(os.environ, {"LLM_PROVIDER": "moonshot", "OPEN_AI_API_KEY": "moon-key"}, clear=True)
    def test_moonshot_provider(self):
        config = _get_llm_config()
        self.assertEqual(config["provider"], "moonshot")
        self.assertEqual(config["model"], "moonshot-v1-32k")

    @patch.dict(os.environ, {"OPEN_AI_API_KEY": "default-key", "OPEN_AI_BASE_URL": "https://custom.com/v1"}, clear=True)
    def test_default_provider_fallback(self):
        config = _get_llm_config()
        self.assertEqual(config["provider"], "default")
        self.assertEqual(config["api_key"], "default-key")
        self.assertEqual(config["base_url"], "https://custom.com/v1")
        self.assertEqual(config["model"], "moonshot-v1-32k")

    @patch.dict(os.environ, {}, clear=True)
    def test_no_key_raises(self):
        with self.assertRaises(ValueError):
            _get_llm_config()

    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax", "MINIMAX_API_KEY": "k", "OPEN_AI_BASE_URL": "https://override.com/v1"}, clear=True)
    def test_preset_base_url_not_overridden_by_openai_base_url(self):
        config = _get_llm_config()
        # Provider presets should use their own base_url, not OPEN_AI_BASE_URL
        self.assertEqual(config["base_url"], "https://api.minimax.io/v1")


class TestGeneratePrompt(unittest.TestCase):
    """Test generate_prompt with mocked OpenAI client."""

    @patch("draw_prompt.load_dotenv")
    @patch("draw_prompt.OpenAI")
    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax", "MINIMAX_API_KEY": "test-key"}, clear=True)
    def test_generate_prompt_minimax(self, mock_openai_cls, mock_dotenv):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps({"result": "A beautiful sunset over the ocean"})
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion

        result = generate_prompt("夕阳西下")
        self.assertEqual(result, "A beautiful sunset over the ocean")

        # Verify OpenAI client was initialized with MiniMax config
        mock_openai_cls.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.minimax.io/v1",
        )

        # Verify temperature was clamped (0.3 is valid for MiniMax, stays 0.3)
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertAlmostEqual(call_kwargs["temperature"], 0.3)
        self.assertEqual(call_kwargs["model"], "MiniMax-M2.7")

    @patch("draw_prompt.load_dotenv")
    @patch("draw_prompt.OpenAI")
    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax", "MINIMAX_API_KEY": "test-key"}, clear=True)
    def test_generate_prompt_strips_think_tags(self, mock_openai_cls, mock_dotenv):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = '<think>let me think about this...</think>{"result": "A serene garden"}'
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion

        result = generate_prompt("花园")
        self.assertEqual(result, "A serene garden")

    @patch("draw_prompt.load_dotenv")
    @patch("draw_prompt.OpenAI")
    @patch.dict(os.environ, {"OPEN_AI_API_KEY": "key", "OPEN_AI_BASE_URL": "https://api.moonshot.cn/v1"}, clear=True)
    def test_generate_prompt_default_provider(self, mock_openai_cls, mock_dotenv):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps({"result": "A mountain landscape"})
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion

        result = generate_prompt("大山")
        self.assertEqual(result, "A mountain landscape")

        mock_openai_cls.assert_called_once_with(
            api_key="key",
            base_url="https://api.moonshot.cn/v1",
        )

    @patch("draw_prompt.load_dotenv")
    @patch("draw_prompt.OpenAI")
    @patch.dict(os.environ, {"OPEN_AI_API_KEY": "key"}, clear=True)
    def test_generate_prompt_api_error(self, mock_openai_cls, mock_dotenv):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        with self.assertRaises(RuntimeError) as ctx:
            generate_prompt("测试")
        self.assertIn("Failed to create completion", str(ctx.exception))

    @patch("draw_prompt.load_dotenv")
    @patch("draw_prompt.OpenAI")
    @patch.dict(os.environ, {"OPEN_AI_API_KEY": "key"}, clear=True)
    def test_generate_prompt_invalid_json(self, mock_openai_cls, mock_dotenv):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "not valid json"
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion

        with self.assertRaises(RuntimeError) as ctx:
            generate_prompt("测试")
        self.assertIn("Failed to parse completion result", str(ctx.exception))


class TestGeneratePromptIntegration(unittest.TestCase):
    """Integration tests that call the real MiniMax API.

    These tests are skipped unless MINIMAX_API_KEY is set in the environment.
    Run with: MINIMAX_API_KEY=your_key python -m pytest tests/test_draw_prompt.py -k Integration -v
    """

    @classmethod
    def setUpClass(cls):
        cls.api_key = os.environ.get("MINIMAX_API_KEY")
        if not cls.api_key:
            raise unittest.SkipTest("MINIMAX_API_KEY not set, skipping integration tests")

    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax"})
    def test_minimax_generates_prompt(self):
        """Test that MiniMax returns a valid image prompt."""
        os.environ["MINIMAX_API_KEY"] = self.api_key
        result = generate_prompt("一个美丽的日落")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 10)

    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax", "LLM_MODEL": "MiniMax-M2.7-highspeed"})
    def test_minimax_highspeed_model(self):
        """Test that MiniMax highspeed model works."""
        os.environ["MINIMAX_API_KEY"] = self.api_key
        result = generate_prompt("一朵花")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 5)

    @patch.dict(os.environ, {"LLM_PROVIDER": "minimax"})
    def test_minimax_returns_english_prompt(self):
        """Test that MiniMax returns English text for Chinese input."""
        os.environ["MINIMAX_API_KEY"] = self.api_key
        result = generate_prompt("城市夜景")
        self.assertIsInstance(result, str)
        # Verify result contains at least some ASCII characters (English)
        ascii_chars = sum(1 for c in result if c.isascii() and c.isalpha())
        self.assertGreater(ascii_chars, 5, "Expected English text in the generated prompt")


if __name__ == "__main__":
    unittest.main()
