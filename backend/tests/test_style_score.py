from app.posting.local_llm import LocalLLMUnavailableError
from app.posting.style import CaptionStyle
from app.posting.style_score import score_caption_style


class FakeLLM:
    def __init__(self, embeddings: dict[str, list[float]] | None = None, unavailable: bool = False):
        self._embeddings = embeddings or {}
        self._unavailable = unavailable

    def embed(self, text: str) -> list[float]:
        if self._unavailable:
            raise LocalLLMUnavailableError("no local model")
        return self._embeddings[text]


def test_returns_none_when_no_example_captions():
    style = CaptionStyle(example_captions=[])
    assert score_caption_style("Some caption", style, FakeLLM()) is None


def test_returns_none_when_llm_unavailable():
    style = CaptionStyle(example_captions=["An example"])
    assert score_caption_style("Some caption", style, FakeLLM(unavailable=True)) is None


def test_identical_embeddings_score_100():
    style = CaptionStyle(example_captions=["Example one"])
    llm = FakeLLM({"New caption": [1.0, 0.0], "Example one": [1.0, 0.0]})
    score = score_caption_style("New caption", style, llm)
    assert score == 100.0


def test_orthogonal_embeddings_score_0():
    style = CaptionStyle(example_captions=["Example one"])
    llm = FakeLLM({"New caption": [1.0, 0.0], "Example one": [0.0, 1.0]})
    score = score_caption_style("New caption", style, llm)
    assert score == 0.0


def test_averages_across_multiple_examples():
    style = CaptionStyle(example_captions=["Example A", "Example B"])
    llm = FakeLLM(
        {
            "New caption": [1.0, 0.0],
            "Example A": [1.0, 0.0],  # similarity 1.0
            "Example B": [0.0, 1.0],  # similarity 0.0
        }
    )
    score = score_caption_style("New caption", style, llm)
    assert score == 50.0
