from pathlib import Path
import pytest

from services.prompt_loader import PromptLoader


def test_loads_existing_yaml_correctly(tmp_path: Path):
    p = tmp_path / "prompts" / "default"
    p.mkdir(parents=True)
    (p / "v1.yaml").write_text("system: sys\ntemplate: 'A {{ repo_tree }} B {{ selected_files }}'")
    loader = PromptLoader(str(tmp_path / "prompts"))
    data = loader.load("default", 1)
    assert data["system"] == "sys"


def test_renders_placeholders_and_system_unmodified(tmp_path: Path):
    p = tmp_path / "prompts" / "default"
    p.mkdir(parents=True)
    (p / "v1.yaml").write_text("system: fixed\ntemplate: 'RT={{ repo_tree }}\nSF={{ selected_files }}'")
    loader = PromptLoader(str(tmp_path / "prompts"))
    rendered = loader.render("default", 1, "tree", "files")
    assert "tree" in rendered["user"] and "files" in rendered["user"]
    assert rendered["system"] == "fixed"


def test_missing_file(tmp_path: Path):
    loader = PromptLoader(str(tmp_path / "prompts"))
    with pytest.raises(FileNotFoundError):
        loader.load("none", 1)


def test_missing_placeholder(tmp_path: Path):
    p = tmp_path / "prompts" / "default"
    p.mkdir(parents=True)
    (p / "v1.yaml").write_text("system: s\ntemplate: 'no placeholders'")
    loader = PromptLoader(str(tmp_path / "prompts"))
    with pytest.raises(ValueError):
        loader.render("default", 1, "tree", "files")
