# -*- coding: utf-8 -*-
"""Shared implementation of the TypeSafe System One protocol."""
from time import perf_counter
from typing import Any, Mapping

from ._base import ClassifierModelBase
from ._question import (
    BinaryQuestion,
    ChoiceQuestion,
    ClassifierQuestion,
    ScoreQuestion,
)
from ._response import (
    BinaryAnswer,
    ChoiceAnswer,
    ClassifierAnswer,
    ClassifierResponse,
    ScoreAnswer,
)
from ._usage import ClassifierUsage
from ..credential import DashScopeCredential, TypeSafeCredential


def _to_sdk_question(question: ClassifierQuestion) -> Any:
    """Translate an AgentScope question to a TypeSafe question."""
    from typesafe_sdk import Choice, Noul, Score

    match question:
        case BinaryQuestion():
            # The binary question maps to TypeSafe's Noul primitive
            criteria = question.criteria and question.criteria.model_dump(
                exclude_unset=True,
            )
            return Noul(instructions=question.instructions, criteria=criteria)
        case ChoiceQuestion():
            return Choice(
                instructions=question.instructions,
                criteria=question.criteria,
            )
        case ScoreQuestion():
            return Score(
                instructions=question.instructions,
                criteria=question.criteria,
            )


def _from_sdk_answer(answer: Any) -> ClassifierAnswer:
    """Translate a TypeSafe answer to an AgentScope answer."""
    match answer.type:
        case "noul":
            return BinaryAnswer(probability=answer.noul)
        case "choice":
            return ChoiceAnswer(
                choice=answer.choice,
                confidence=answer.confidence,
                probabilities=dict(answer.probabilities),
            )
        case "score":
            return ScoreAnswer(
                score=answer.score,
                confidence=answer.confidence,
                legend=dict(answer.legend),
                probabilities=dict(answer.probabilities),
            )
    raise ValueError(f"Unsupported TypeSafe answer type: {answer.type!r}.")


class _SystemOneClassifierModel(ClassifierModelBase):
    """Common SDK client and question/answer translation for System One."""

    def __init__(
        self,
        credential: TypeSafeCredential | DashScopeCredential,
        model: str,
        parameters: ClassifierModelBase.Parameters | None,
        timeout: float,
        max_retries: int,
        retry_delay: float,
        *,
        base_url: str | None,
        dependency_extra: str,
    ) -> None:
        """Initialize the shared client using provider-specific settings."""
        try:
            from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy
        except ImportError as error:
            raise ImportError(
                f"{type(self).__name__} requires a compatible optional "
                "'typesafe-sdk' dependency. Install it with "
                f"`pip install 'agentscope[{dependency_extra}]'`.",
            ) from error

        super().__init__(credential, model, parameters)
        self.client = AsyncTypeSafeClient(
            api_key=credential.api_key.get_secret_value(),
            base_url=base_url,
            model=model,
            timeout=timeout,
            retry=RetryPolicy(
                max_retries=max_retries,
                backoff_initial=retry_delay,
            ),
        )

    async def __call__(
        self,
        state: str | dict,
        questions: Mapping[str, ClassifierQuestion],
        **kwargs: Any,
    ) -> ClassifierResponse:
        """Call the TypeSafe System One API and normalize its response.

        Args:
            state (`str | dict`):
                The text or JSON content to classify.
            questions (`Mapping[str, ClassifierQuestion]`):
                The typed questions keyed by name.
            **kwargs (`Any`):
                Per-call TypeSafe options, e.g. ``extra_headers`` and
                ``extra_body``.

        Returns:
            `ClassifierResponse`:
                The typed probabilistic answers keyed by question name.
        """
        start_time = perf_counter()
        response = await self.client.system_one(
            state=state,
            questions={
                name: _to_sdk_question(question)
                for name, question in questions.items()
            },
            model=self.model,
            **kwargs,
        )
        return ClassifierResponse(
            model=response.model,
            content={
                name: _from_sdk_answer(answer)
                for name, answer in response.answers.items()
            },
            usage=ClassifierUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                time=perf_counter() - start_time,
            ),
        )
