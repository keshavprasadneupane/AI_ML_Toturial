from dataclasses import asdict, fields, is_dataclass
from json import JSONDecodeError, dump, load
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def read_params(config_path: Path, config_class: type[T]) -> T:
	"""Load config parameters from a JSON file into a dataclass schema."""
	if not is_dataclass(config_class):
		raise TypeError(f"Target schema '{config_class}' is not a valid dataclass.")

	try:
		with open(config_path, "r", encoding="utf-8") as config_file:
			config_data = load(config_file)

		if not config_data or not isinstance(config_data, dict):
			raise ValueError(f"Config file '{config_path}' is empty or invalid.")

		allowed_keys = {f.name for f in fields(config_class)}
		unknown_keys = set(config_data.keys()) - allowed_keys
		if unknown_keys:
			raise ValueError(
				f"Unknown parameter(s) in '{config_path}': {', '.join(unknown_keys)}"
			)

		return config_class(**config_data)

	except FileNotFoundError as e:
		raise FileNotFoundError(f"Configuration file '{config_path}' not found.") from e
	except JSONDecodeError as e:
		raise ValueError(f"Malformed JSON in '{config_path}'.") from e
	except TypeError as e:
		raise TypeError(f"Schema mismatch in '{config_path}'.\nDetails: {e}") from e
	except (FileNotFoundError, ValueError):
		raise
	except Exception as e:
		raise RuntimeError(f"Error reading configuration file '{config_path}': {e}") from e


def create_default_config(config_path: Path, config_class: type[T]) -> T:
	"""Create, save, and return a default config instance when none exists."""
	factory = getattr(config_class, "get_default", config_class)
	default_config: T = factory()

	config_path.parent.mkdir(parents=True, exist_ok=True)

	try:
		with open(config_path, "w", encoding="utf-8") as f:
			dump(asdict(default_config), f, indent=4, default=str)
	except Exception as e:
		raise OSError(f"Could not save default config to '{config_path}': {e}") from e

	return default_config