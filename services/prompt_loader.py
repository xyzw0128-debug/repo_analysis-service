from pathlib import Path


def _parse_simple_yaml(text: str):
    data = {}
    for line in text.splitlines():
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        data[k.strip()] = v.strip().strip('"')
    return data


class PromptLoader:
    def __init__(self, prompts_root: str = 'prompts'):
        self.prompts_root = Path(prompts_root)

    def load(self, name: str, version: int):
        path = self.prompts_root / name / f'v{version}.yaml'
        if not path.exists():
            raise FileNotFoundError(path)
        data = _parse_simple_yaml(path.read_text())
        if 'system' not in data or 'template' not in data:
            raise KeyError('Prompt YAML must contain system and template fields')
        return data

    def render(self, name: str, version: int, repo_tree: str, selected_files: str):
        prompt = self.load(name, version)
        template = prompt['template']
        if '{{ repo_tree }}' not in template or '{{ selected_files }}' not in template:
            raise ValueError('Template must include {{ repo_tree }} and {{ selected_files }} placeholders')
        return {'system': prompt['system'], 'user': template.replace('{{ repo_tree }}', repo_tree).replace('{{ selected_files }}', selected_files)}
