from app.services.normalizers import (
    extract_account_id,
    extract_avatar_url,
    extract_display_name,
    extract_match_id,
    extract_result,
)


def test_profile_normalizers_support_common_steam_fields() -> None:
    profile = {
        "account_id": "123",
        "personaname": "Pocket Main",
        "avatarfull": "https://example.test/avatar.png",
    }

    assert extract_account_id(profile) == 123
    assert extract_display_name(profile) == "Pocket Main"
    assert extract_avatar_url(profile) == "https://example.test/avatar.png"


def test_match_normalizers_support_common_fields() -> None:
    match = {"match_id": "456", "win": True}

    assert extract_match_id(match) == 456
    assert extract_result(match) == "win"
