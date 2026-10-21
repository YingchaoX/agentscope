# -*- coding: utf-8 -*-
"""The TypeSafe Jev classifier model implementation."""
from pydantic import ConfigDict

from .._base import ClassifierModelBase
from .._system_one import _SystemOneClassifierModel
from ...credential import TypeSafeCredential


class JevClassifierModel(_SystemOneClassifierModel):
    """A classifier backed by TypeSafe's Jev System One API."""

    class Parameters(ClassifierModelBase.Parameters):
        """Provider-specific Jev model parameters."""

        model_config = ConfigDict(extra="forbid")

    def __init__(
        self,
        credential: TypeSafeCredential,
        model: str = "jev-latest",
        parameters: "JevClassifierModel.Parameters | None" = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_delay: float = 0.5,
    ) -> None:
        """Initialize the Jev classifier.

        Args:
            credential (`TypeSafeCredential`):
                The TypeSafe API credential.
            model (`str`, defaults to ``"jev-latest"``):
                The Jev model name or alias.
            parameters (`JevClassifierModel.Parameters | None`):
                Provider-specific model parameters.
            timeout (`float`, defaults to `30.0`):
                Per-request timeout in seconds.
            max_retries (`int`, defaults to `2`):
                Maximum retries after the initial request, done by the SDK.
            retry_delay (`float`, defaults to `0.5`):
                Initial exponential backoff delay in seconds.
        """
        super().__init__(
            credential,
            model,
            parameters,
            timeout,
            max_retries,
            retry_delay,
            base_url=credential.base_url,
            dependency_extra="classifier-jev",
        )
