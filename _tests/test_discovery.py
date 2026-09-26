"""discovery must fail loudly on a wrong site root, not turn content tests into skips."""

import discovery
import pytest


def test_wrong_site_root_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(discovery, "DOCS", tmp_path)
    with pytest.raises(FileNotFoundError):
        discovery.post_paths()


def test_absent_collection_folder_is_empty(monkeypatch, tmp_path):
    """Git doesn't track empty dirs, so a missing _previews/ is a legitimate state."""
    (tmp_path / "_config.yml").write_text("title: fixture\n")
    monkeypatch.setattr(discovery, "DOCS", tmp_path)
    assert discovery.preview_paths() == []
