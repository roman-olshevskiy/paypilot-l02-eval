"""Offline regression checks for upstream API/model configuration changes."""
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import l02_eval as E


class UpstreamCompatibility(unittest.TestCase):
    def test_customer_is_sent_as_separate_session_field(self):
        module = types.ModuleType("deepeval.test_case")
        module.LLMTestCase = object
        response = {"request_id": "offline", "answer": "answer",
                    "usage": {"input_tokens": 0, "output_tokens": 0}}
        tree = {"name": "root", "children": []}
        with patch.dict(sys.modules, {"deepeval.test_case": module}), \
             patch.object(E, "stand", side_effect=[response, tree]) as api:
            E.run_case({"id": "test", "input": "Balance?", "customer_id": "CUS-0001"},
                       None, set(), ("anthropic", "unused"))
        self.assertEqual(api.call_args_list[0].args,
                         ("POST", "/chat", {"message": "Balance?", "customer_id": "CUS-0001"}))

    def test_new_model_family_omits_temperature_and_supplies_prices(self):
        class FakeModel:
            def __init__(self, **kwargs):
                self.config = kwargs
        models = types.ModuleType("deepeval.models")
        models.AnthropicModel = models.OpenAIModel = models.GeminiModel = FakeModel
        for name in ["claude-haiku-5-5", "claude-haiku-5-5-20261001",
                     "anthropic/claude-haiku-5-5"]:
            with self.subTest(name=name), patch.dict(sys.modules, {"deepeval.models": models}):
                config = E.make_judge("anthropic", name).config
                self.assertNotIn("temperature", config)
                self.assertEqual(config["cost_per_input_token"], 0.1 / 1e6)
                self.assertEqual(config["cost_per_output_token"], 0.5 / 1e6)

    def test_historical_model_is_not_repriced_as_new_family(self):
        self.assertEqual(E.anthropic_model_facts("claude-haiku-4-5"), {})
