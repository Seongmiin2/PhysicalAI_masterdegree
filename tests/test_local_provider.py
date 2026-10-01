import io
import json
from urllib.error import URLError
from unittest.mock import MagicMock

import pytest

from providers.base import GenerationRequest
from providers.local import LocalProvider, LocalProviderError, _NoRedirect


@pytest.fixture
def provider(monkeypatch):
    for key in ("CHUM_LOCAL_MODEL", "CHUM_OLLAMA_URL", "CHUM_LOCAL_TIMEOUT_SECONDS", "CHUM_LOCAL_NUM_GPU"):
        monkeypatch.delenv(key, raising=False)
    result = LocalProvider()
    result._opener = MagicMock()
    return result


def request():
    return GenerationRequest("reviewer", {"question": "Next experiment?"}, {
        "evidence": [{"chunk_id": "roadmap:1", "text": "Compare windows 60 and 120."}],
    })


def response(provider, **changes):
    content = {"summary": "Planning only", "recommendation": "Compare windows",
               "needs_human_review": False, "citations": ["roadmap:1"]} | changes
    envelope = {"done": True, "message": {"content": json.dumps(content)}}
    provider._opener.open.return_value = io.BytesIO(json.dumps(envelope).encode())


def test_local_generation_is_grounded_suggestion(provider):
    response(provider)
    result = provider.generate(request())
    assert result["provenance"] == "LOCAL_MODEL_SUGGESTION"
    assert result["citations"] == ["roadmap:1"]
    sent = provider._opener.open.call_args
    payload = json.loads(sent.args[0].data)
    assert sent.args[0].full_url == "http://127.0.0.1:11434/api/chat"
    assert payload["keep_alive"] == 0
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["format"]["additionalProperties"] is False
    assert sent.kwargs["timeout"] == 120


@pytest.mark.parametrize("changes", [
    {"citations": ["invented:1"]}, {"citations": [1]}, {"citations": "roadmap:1"},
    {"needs_human_review": "false"}, {"summary": []}, {"recommendation": ""},
    {"approval": True},
])
def test_invalid_output_is_rejected(provider, changes):
    response(provider, **changes)
    with pytest.raises(LocalProviderError):
        provider.generate(request())


def test_ungrounded_suggestion_requires_review(provider):
    response(provider, citations=[])
    assert provider.generate(request())["needs_human_review"] is True


@pytest.mark.parametrize("exception", [TimeoutError(), URLError("offline")])
def test_inference_failure_is_explicit(provider, exception):
    provider._opener.open.side_effect = exception
    with pytest.raises(LocalProviderError, match="Local inference failed"):
        provider.generate(request())


@pytest.mark.parametrize("envelope", [
    {"done": True, "message": {"content": "not json"}},
    {"done": False, "message": {"content": "{}"}},
    {"done": True, "message": {"content": "[]"}},
    {"done": True, "message": {"content": "{}", "tool_calls": [{"name": "run"}]}},
    {"done": True, "done_reason": "length", "message": {"content": "{}"}},
])
def test_bad_envelope_is_rejected(provider, envelope):
    provider._opener.open.return_value = io.BytesIO(json.dumps(envelope).encode())
    with pytest.raises(LocalProviderError):
        provider.generate(request())


@pytest.mark.parametrize("url", ["https://example.com", "http://localhost:11434",
    "http://127.0.0.1:11434/redirect", "http://127.0.0.1@evil.example:11434"])
def test_remote_endpoint_rejected(monkeypatch, url):
    monkeypatch.setenv("CHUM_OLLAMA_URL", url)
    with pytest.raises(ValueError, match="loopback"):
        LocalProvider()


def test_redirect_rejected():
    with pytest.raises(LocalProviderError, match="redirect"):
        _NoRedirect().redirect_request(None, None, 302, "", {}, "http://example.com")


def test_cpu_configuration(monkeypatch):
    monkeypatch.setenv("CHUM_LOCAL_NUM_GPU", "0")
    monkeypatch.setenv("CHUM_LOCAL_MODEL", "qwen3:4b")
    provider = LocalProvider()
    assert provider.options["num_gpu"] == 0
    assert provider.model == "qwen3:4b"


@pytest.mark.parametrize("value", ["nan", "inf", "0", "-1"])
def test_invalid_timeout_rejected(monkeypatch, value):
    monkeypatch.setenv("CHUM_LOCAL_TIMEOUT_SECONDS", value)
    with pytest.raises(ValueError):
        LocalProvider()


def test_role_prompt_and_citation_enum(provider):
    response(provider)
    provider.generate(request())
    payload = json.loads(provider._opener.open.call_args.args[0].data)
    assert "As reviewer" in payload["messages"][0]["content"]
    assert "context.current_state" in payload["messages"][0]["content"]
    assert payload["format"]["properties"]["citations"]["items"]["enum"] == ["roadmap:1"]
    assert payload["options"]["num_predict"] == 1024


def test_reviewer_copy_requires_human_review(provider):
    response(provider)
    req = request()
    req.context["proposal_to_critique"] = {"recommendation": "Compare windows"}
    assert provider.generate(req)["needs_human_review"] is True


@pytest.mark.parametrize("changes", [{"summary": "x" * 121}, {"recommendation": "x" * 181},
    {"citations": ["roadmap:1"] * 4}])
def test_output_limits_validated(provider, changes):
    response(provider, **changes)
    with pytest.raises(LocalProviderError):
        provider.generate(request())
