# -*- coding: utf-8 -*-
"""The DashScope System One classifier model implementation."""
from pydantic import ConfigDict

from .._base import ClassifierModelBase
from .._system_one import _SystemOneClassifierModel
from ...credential import DashScopeCredential


class DashScopeClassifierModel(_SystemOneClassifierModel):
    """A classifier backed by Alibaba Cloud Model Studio's System One API.

    Install the optional dependency with
    ``pip install 'agentscope[classifiers]'``.
    Configure :class:`DashScopeCredential` with your workspace's regional
    endpoint, ending in ``/compatible-mode/v1``. The SDK's
    ``/compatible-mode`` form is also accepted. The credential is not modified.

    .. note::
        ``decision-model-preview`` is a preview model. Its availability and
        supported endpoints are determined by Alibaba Cloud Model Studio.
    """

    class Parameters(ClassifierModelBase.Parameters):
        """Provider-specific DashScope classifier parameters."""

        model_config = ConfigDict(extra="forbid")

    def __init__(
        self,
        credential: DashScopeCredential,
        model: str = "decision-model-preview",
        parameters: "DashScopeClassifierModel.Parameters | None" = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_delay: float = 0.5,
    ) -> None:
        """Initialize the DashScope classifier.

        Args:
            credential (`DashScopeCredential`):
                The DashScope API key and compatible-mode endpoint.
            model (`str`, defaults to ``"decision-model-preview"``):
                The decision model name.
            parameters (`DashScopeClassifierModel.Parameters | None`):
                Provider-specific model parameters.
            timeout (`float`, defaults to `30.0`):
                Per-request timeout in seconds.
            max_retries (`int`, defaults to `2`):
                Maximum retries after the initial request, done by the SDK.
            retry_delay (`float`, defaults to `0.5`):
                Initial exponential backoff delay in seconds.
        """
        # The TypeSafe SDK appends /v1/systemone to its API root.
        base_url = credential.base_url.rstrip("/").removesuffix("/v1")
        super().__init__(
            credential,
            model,
            parameters,
            timeout,
            max_retries,
            retry_delay,
            base_url=base_url,
            dependency_extra="classifiers",
        )
