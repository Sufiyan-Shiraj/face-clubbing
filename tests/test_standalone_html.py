"""Tests for zero-dependency standalone HTML gallery generator (SPEC rev 3, Decision 20)."""

import json
import re
from backend.engine.standalone_html import generate_standalone_gallery_html


def test_generate_standalone_gallery_html_structure():
    sample_people = {
        "version": 1,
        "generated_at": "2026-10-14T05:00:00Z",
        "photos": {
            "photo_001": {"file_name": "event_01.jpg", "face_count": 2},
            "photo_002": {"file_name": "event_02.jpg", "face_count": 0},
        },
        "people": [
            {
                "id": "person_abc",
                "label": "Organizer",
                "photo_ids": ["photo_001"],
                "face_ids": ["f_photo_001_0"],
                "representative_face": "faces/f_photo_001_0.jpg",
                "photo_count": 1,
            }
        ],
        "unrecognized": {
            "photo_ids": ["photo_002"],
            "faces": [
                {
                    "face_id": "f_photo_001_1",
                    "photo_id": "photo_001",
                    "file_name": "event_01.jpg",
                    "face": "faces/f_photo_001_1.jpg",
                    "rejection_reason": "small_face",
                    "det_score": 0.55,
                }
            ],
        },
    }

    sample_config = {
        "title": "Tech Conference 2026",
        "subtitle": "AI & Robotics Summit",
        "accent": "#6366f1",
        "footer": "Exported via PhotoSorter",
        "show_labels": True,
        "include_maybe": False,
        "hide_single_photo_default": False,
    }

    html = generate_standalone_gallery_html(sample_people, sample_config)

    # 1. Basic HTML document validity
    assert "<!DOCTYPE html>" in html
    assert "<html lang=\"en\" class=\"dark\">" in html
    assert "Tech Conference 2026" in html
    assert "AI & Robotics Summit" in html
    assert "#6366f1" in html
    assert "Exported via PhotoSorter" in html

    # 2. Extract and parse embedded JSON
    people_match = re.search(r'<script\s+id="gallery-data"\s+type="application/json">\s*(\{.*?\})\s*</script>', html, re.DOTALL)
    assert people_match is not None, "gallery-data JSON script tag not found in HTML"
    parsed_people = json.loads(people_match.group(1))
    assert parsed_people["version"] == 1
    assert len(parsed_people["people"]) == 1
    assert parsed_people["people"][0]["id"] == "person_abc"
    assert parsed_people["unrecognized"]["photo_ids"] == ["photo_002"]

    config_match = re.search(r'<script\s+id="gallery-config"\s+type="application/json">\s*(\{.*?\})\s*</script>', html, re.DOTALL)
    assert config_match is not None, "gallery-config JSON script tag not found in HTML"
    parsed_config = json.loads(config_match.group(1))
    assert parsed_config["title"] == "Tech Conference 2026"
    assert parsed_config["accent"] == "#6366f1"

    # 3. Verify zero external JavaScript dependencies (no <script src=...)
    external_scripts = re.findall(r"<script\s+[^>]*src=", html, re.IGNORECASE)
    assert len(external_scripts) == 0, f"Found unexpected external script tags: {external_scripts}"

    # 4. Interactive UI components present in DOM template
    assert 'data-tab="people"' in html
    assert 'data-tab="photos"' in html
    assert 'data-tab="unrecognized"' in html
    assert 'id="view-people"' in html
    assert 'id="view-photos"' in html
    assert 'id="view-unrecognized"' in html
    assert 'id="search-input"' in html
    assert 'id="person-modal"' in html
    assert 'id="lightbox"' in html
