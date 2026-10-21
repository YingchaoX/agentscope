# -*- coding: utf-8 -*-
"""Tests for DashScope-specific System One configuration and responses."""
from dataclasses import asdict
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import pytest

from utils import AnyValue
from agentscope.classifier import BinaryQuestion, DashScopeClassifierModel
from agentscope.credential import DashScopeCredential

typesafe_sdk = pytest.importorskip("typesafe_sdk")


class DashScopeClassifierModelTest(IsolatedAsyncioTestCase):
    """Cover provider differences; Jev tests cover shared translations."""

    @patch("typesafe_sdk.AsyncTypeSafeClient")
    async def test_client_configuration(self, client_cls: Any) -> None:
        """Normalize version suffixes without modifying the credential."""
        root = "https://workspace.example/compatible-mode"
        for suffix in ("", "/", "/v1", "/v1/"):
            with self.subTest(suffix=suffix):
                credential = DashScopeCredential(
                    api_key="secret",
                    base_url=root + suffix,
                )
                model = DashScopeClassifierModel(credential)
                self.assertIs(model.credential, credential)
                self.assertEqual(credential.base_url, root + suffix)
                self.assertDictEqual(
                    client_cls.call_args.kwargs,
                    {
                        "api_key": "secret",
                        "base_url": root,
                        "model": "decision-model-preview",
                        "timeout": 30.0,
                        "retry": typesafe_sdk.RetryPolicy(),
                    },
                )

    async def test_call_without_output_tokens(self) -> None:
        """Use the real SDK to check the URL and parse input-only usage."""
        import httpx2

        requests = []

        def handle(request: httpx2.Request) -> httpx2.Response:
            requests.append(request)
            return httpx2.Response(
                200,
                json={
                    "model": "decision-model-preview",
                    "answers": {"urgent": {"type": "noul", "noul": 0.8}},
                    "usage": {"input_tokens": 120},
                },
            )

        client_cls = typesafe_sdk.AsyncTypeSafeClient
        with patch(
            "typesafe_sdk.AsyncTypeSafeClient",
            side_effect=lambda **kwargs: client_cls(
                transport=httpx2.MockTransport(handle),
                **kwargs,
            ),
        ):
            model = DashScopeClassifierModel(
                DashScopeCredential(
                    api_key="secret",
                    base_url="https://workspace.example/compatible-mode/v1",
                ),
            )
        try:
            response = await model("hello", {"urgent": BinaryQuestion()})
        finally:
            await model.client.aclose()

        self.assertEqual(len(requests), 1)
        self.assertEqual(
            str(requests[0].url),
            "https://workspace.example/compatible-mode/v1/systemone",
        )
        self.assertDictEqual(
            asdict(response),
            {
                "model": "decision-model-preview",
                "content": {
                    "urgent": {"type": "binary_answer", "probability": 0.8},
                },
                "usage": {
                    "time": AnyValue(),
                    "input_tokens": 120,
                    "output_tokens": None,
                    "type": "classifier",
                },
                "id": AnyValue(),
                "created_at": AnyValue(),
                "type": "classifier_response",
                "metadata": {},
            },
        )
