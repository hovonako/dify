from openai import BadRequestError, OpenAI, AzureOpenAI
from openai.types import Completion as CompletionMessage
from openai._types import NotGiven, NOT_GIVEN
from openai.types.completion import CompletionChoice
from openai.types.completion_usage import CompletionUsage
from openai.resources.completions import Completions

# import monkeypatch
from typing import List, Any, Generator, Union, Optional, Literal
from time import time, sleep

from core.model_runtime.errors.invoke import InvokeAuthorizationError

import re

class MockCompletionsClass(object):
    @staticmethod
    def mocked_openai_completion_create_sync(
        model: str
    ) -> CompletionMessage:
        sleep(1)
        return CompletionMessage(
            id="cmpl-3QJQa5jXJ5Z5X",
            object="text_completion",
            created=int(time()),
            model=model,
            system_fingerprint="",
            choices=[
                CompletionChoice(
                    text="mock",
                    index=0,
                    logprobs=None,
                    finish_reason="stop",
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=2,
                completion_tokens=1,
                total_tokens=3,
            )
        )
    
    @staticmethod
    def mocked_openai_completion_create_stream(
        model: str
    ) -> Generator[CompletionMessage, None, None]:
        full_text = "Hello, world!\n\n```python\nprint('Hello, world!')\n```"
        for i in range(0, len(full_text) + 1):
            sleep(0.1)
            if i == len(full_text):
                yield CompletionMessage(
                    id="cmpl-3QJQa5jXJ5Z5X",
                    object="text_completion",
                    created=int(time()),
                    model=model,
                    system_fingerprint="",
                    choices=[
                        CompletionChoice(
                            text="",
                            index=0,
                            logprobs=None,
                            finish_reason="stop",
                        )
                    ],
                    usage=CompletionUsage(
                        prompt_tokens=2,
                        completion_tokens=17,
                        total_tokens=19,
                    ),
                )
            else:
                yield CompletionMessage(
                    id="cmpl-3QJQa5jXJ5Z5X",
                    object="text_completion",
                    created=int(time()),
                    model=model,
                    system_fingerprint="",
                    choices=[
                        CompletionChoice(
                            text=full_text[i],
                            index=0,
                            logprobs=None,
                            finish_reason="content_filter"
                        )
                    ],
                )

    def completion_create(self: Completions, *, model: Union[
            str, Literal["babbage-002", "davinci-002", "gpt-3.5-turbo-instruct",
                "text-davinci-003", "text-davinci-002", "text-davinci-001",
                "code-davinci-002", "text-curie-001", "text-babbage-001",
                "text-ada-001"],
        ],
        prompt: Union[str, List[str], List[int], List[List[int]], None],
        stream: Optional[Literal[False]] | NotGiven = NOT_GIVEN,
        **kwargs: Any
    ):
        openai_models = [
            "babbage-002", "davinci-002", "gpt-3.5-turbo-instruct", "text-davinci-003", "text-davinci-002", "text-davinci-001",
            "code-davinci-002", "text-curie-001", "text-babbage-001", "text-ada-001",
        ]
        azure_openai_models = [
            "gpt-35-turbo-instruct"
        ]

        if not re.match(r'^(https?):\/\/[^\s\/$.?#].[^\s]*$', self._client.base_url.__str__()):
            raise InvokeAuthorizationError('Invalid base url')
        if model in openai_models + azure_openai_models:
            if not re.match(r'sk-[a-zA-Z0-9]{24,}$', self._client.api_key) and type(self._client) == OpenAI:
                # sometime, provider use OpenAI compatible API will not have api key or have different api key format
                # so we only check if model is in openai_models
                raise InvokeAuthorizationError('Invalid api key')
            if len(self._client.api_key) < 18 and type(self._client) == AzureOpenAI:
                raise InvokeAuthorizationError('Invalid api key')
            
        if not prompt:
            raise BadRequestError('Invalid prompt')
        if stream:
            return MockCompletionsClass.mocked_openai_completion_create_stream(model=model)
        
        return MockCompletionsClass.mocked_openai_completion_create_sync(model=model)