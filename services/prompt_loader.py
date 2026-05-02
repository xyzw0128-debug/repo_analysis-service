from pathlib import Path


def _simple_yaml(text: str) -> dict:
    out = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        val = v.lstrip()
        if key == "template":
            rest = [val]
            i += 1
            while i < len(lines) and ":" not in lines[i].split(" ", 1)[0]:
                rest.append(lines[i])
                i += 1
            val = "\n".join(rest)
            out[key] = val.strip().strip("'\"")
            continue
        out[key] = val.strip().strip("'\"")
        i += 1
    return out


class PromptLoader:
    def __init__(self, prompt_root: str = "prompts"):
        self.prompt_root = Path(prompt_root)

    def load(self, name: str, version: int | str) -> dict:
        path = self.prompt_root / name / f"v{version}.yaml"
        if not path.exists():
            raise FileNotFoundError(path)
        data = _simple_yaml(path.read_text())
        if "system" not in data or "template" not in data:
            raise KeyError("Missing system or template")
        return data

    def render(self, name: str, version: int | str, repo_tree: str, selected_files: str) -> dict:
        d = self.load(name, version)
        t = d["template"]
        if "{{ repo_tree }}" not in t or "{{ selected_files }}" not in t:
            raise ValueError("Template missing placeholders")
        return {"system": d["system"], "user": t.replace("{{ repo_tree }}", repo_tree).replace("{{ selected_files }}", selected_files)}
