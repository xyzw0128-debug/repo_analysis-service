from pathlib import Path
import pytest
from services.prompt_loader import PromptLoader


def test_loads_existing_yaml_correctly(tmp_path: Path):
    p = tmp_path / 'prompts' / 'analysis'
    p.mkdir(parents=True)
    (p / 'v1.yaml').write_text('system: sys\ntemplate: "A {{ repo_tree }} B {{ selected_files }}"\n')
    loader = PromptLoader(str(tmp_path / 'prompts'))
    data = loader.load('analysis', 1)
    assert data['system'] == 'sys'


def test_renders_placeholders_and_system_unmodified(tmp_path: Path):
    p = tmp_path / 'prompts' / 'analysis'
    p.mkdir(parents=True)
    (p / 'v1.yaml').write_text('system: fixed\ntemplate: "R={{ repo_tree }}\\nF={{ selected_files }}"\n')
    loader = PromptLoader(str(tmp_path / 'prompts'))
    out = loader.render('analysis', 1, 'tree', 'files')
    assert 'R=tree' in out['user']
    assert 'F=files' in out['user']
    assert out['system'] == 'fixed'


def test_missing_file_raises(tmp_path: Path):
    loader = PromptLoader(str(tmp_path / 'prompts'))
    with pytest.raises(FileNotFoundError):
        loader.load('missing', 1)


def test_missing_placeholder_raises(tmp_path: Path):
    p = tmp_path / 'prompts' / 'analysis'
    p.mkdir(parents=True)
    (p / 'v1.yaml').write_text('system: x\ntemplate: "only {{ repo_tree }}"\n')
    loader = PromptLoader(str(tmp_path / 'prompts'))
    with pytest.raises(ValueError):
        loader.render('analysis', 1, 'tree', 'files')
