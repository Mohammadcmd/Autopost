from datetime import date

from app.events.base import EventInfo
from app.posting.caption import generate_caption, generate_template_caption
from app.posting.local_llm import LocalLLMUnavailableError, build_caption_prompt
from app.posting.style import CaptionStyle


class FakeLLM:
    def __init__(self, response: str | None = None, raise_unavailable: bool = False):
        self._response = response
        self._raise_unavailable = raise_unavailable
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        if self._raise_unavailable:
            raise LocalLLMUnavailableError("no local model")
        return self._response


def make_event(**overrides) -> EventInfo:
    defaults = dict(name="Summer Picnic", description="Annual picnic", location="Riverside Park")
    defaults.update(overrides)
    return EventInfo(**defaults)


def test_template_caption_includes_location_and_organizations():
    event = make_event()
    caption = generate_template_caption(
        event, date(2024, 7, 4), 5, organizations=["Rotary Club", "City Parks"]
    )
    assert "Riverside Park" in caption
    assert "Rotary Club" in caption
    assert "City Parks" in caption


def test_template_caption_handles_no_matched_event():
    caption = generate_template_caption(None, date(2024, 7, 4), 3)
    assert "3 moments" in caption


def test_generate_caption_falls_back_to_template_when_llm_unavailable():
    event = make_event()
    llm = FakeLLM(raise_unavailable=True)
    caption = generate_caption(
        event, date(2024, 7, 4), 5, organizations=["Rotary Club"], hashtags=["#fun"], llm=llm
    )
    assert "Riverside Park" in caption
    assert "Rotary Club" in caption
    assert "#fun" in caption


def test_generate_caption_uses_llm_output_when_available():
    event = make_event()
    llm = FakeLLM(response="A beautiful day out with friends and family.")
    caption = generate_caption(event, date(2024, 7, 4), 5, hashtags=["#community"], llm=llm)
    assert "A beautiful day out with friends and family." in caption
    assert llm.last_prompt is not None


def test_generate_caption_enforces_missing_location_and_organizations():
    # The "AI" forgets to mention the location and one organization.
    event = make_event()
    llm = FakeLLM(response="Such a fun time with everyone who came out!")
    caption = generate_caption(
        event,
        date(2024, 7, 4),
        5,
        organizations=["Rotary Club", "City Parks"],
        hashtags=["#fun", "#community"],
        llm=llm,
    )
    assert "Riverside Park" in caption
    assert "Rotary Club" in caption
    assert "City Parks" in caption
    assert "#fun" in caption
    assert "#community" in caption


def test_generate_caption_does_not_duplicate_already_present_requirements():
    event = make_event()
    llm = FakeLLM(response="What a day at Riverside Park with Rotary Club! #fun")
    caption = generate_caption(
        event, date(2024, 7, 4), 5, organizations=["Rotary Club"], hashtags=["#fun"], llm=llm
    )
    assert caption.count("Riverside Park") == 1
    assert caption.count("Rotary Club") == 1
    assert caption.count("#fun") == 1


def test_build_caption_prompt_labels_examples_as_style_reference_only():
    style = CaptionStyle(tone_notes="Casual and upbeat.", example_captions=["Best day ever! ☀️"])
    prompt = build_caption_prompt(
        style=style,
        event_name="Summer Picnic",
        date_str="July 4, 2024",
        location="Riverside Park",
        organizations=["Rotary Club"],
        description="",
        photo_count=5,
        hashtags=["#fun"],
    )
    assert "never copy this text" in prompt
    assert "Best day ever!" in prompt
    assert "Riverside Park" in prompt
    assert "Rotary Club" in prompt
    assert "#fun" in prompt
