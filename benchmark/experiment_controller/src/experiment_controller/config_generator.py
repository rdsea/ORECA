import pathlib

from jinja2 import Environment, FileSystemLoader


def format_yaml_args(args_dict):
    """Format a dictionary as properly indented YAML lines"""
    lines = []
    for key, value in args_dict.items():
        # Properly quote strings
        if isinstance(value, str) and not (
            value.startswith('"') or value.startswith("'")
        ):
            formatted_value = f'"{value}"'
        else:
            formatted_value = str(value)
        lines.append(f"      {key}: {formatted_value}")
    return "\n".join(lines)


env = Environment(
    loader=FileSystemLoader(pathlib.Path(__file__).parent),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.filters["format_yaml_args"] = format_yaml_args
template = env.get_template("experiment_config_template.yaml.j2")


def write_config_to_filepath(data: dict, write_path: pathlib.Path):
    rendered_yaml = template.render(data)
    with open(write_path, "w") as f:
        f.write(rendered_yaml)
