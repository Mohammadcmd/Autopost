from app.posting.facebook import FacebookClient
from app.posting.instagram import InstagramClient


def test_instagram_client_dry_run_without_credentials():
    client = InstagramClient(access_token="", ig_business_account_id="")
    assert client.dry_run is True

    result = client.create_post(["https://example.com/photo.jpg"], "Hello world")
    assert result["dry_run"] is True
    assert result["platform"] == "instagram"
    assert len(result["requests"]) == 2  # container create + publish


def test_instagram_client_dry_run_carousel_for_multiple_photos():
    client = InstagramClient(access_token="", ig_business_account_id="")
    result = client.create_post(
        ["https://example.com/1.jpg", "https://example.com/2.jpg"], "Caption"
    )
    assert result["dry_run"] is True
    # 2 item containers + 1 carousel container + 1 publish call
    assert len(result["requests"]) == 4


def test_instagram_client_requires_at_least_one_image():
    client = InstagramClient(access_token="", ig_business_account_id="")
    try:
        client.create_post([], "Caption")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_facebook_client_dry_run_without_credentials(tmp_path):
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"not a real jpeg, just bytes")

    client = FacebookClient(access_token="", page_id="")
    assert client.dry_run is True

    result = client.post_album("Test Event", [photo], "Caption")
    assert result["album"]["dry_run"] is True
    assert result["photos"][0]["dry_run"] is True


def test_facebook_client_is_live_when_credentials_present():
    client = FacebookClient(access_token="token123", page_id="page123")
    assert client.dry_run is False
