import sys
from dataclasses import asdict, fields, is_dataclass
from json import JSONDecodeError, dump, load
from pathlib import Path
from typing import Type, TypeVar

T = TypeVar("T")

def read_params(config_path: Path, config_class: Type[T]) -> T:
	"""Load configuration parameters from a JSON file into any dataclass schema."""
	if not is_dataclass(config_class):
		print(f"Error: Target schema '{config_class}' is not a valid dataclass.", file=sys.stderr)
		sys.exit(1)

	try:
		with open(config_path, "r", encoding="utf-8") as config_file:
			config_data = load(config_file)

		if not config_data or not isinstance(config_data, dict):
			print(f"Error: Config file '{config_path}' is empty or invalid.", file=sys.stderr)
			sys.exit(1)

		allowed_keys = {f.name for f in fields(config_class)}
		unknown_keys = set(config_data.keys()) - allowed_keys
		if unknown_keys:
			print(
				f"Error: Unknown parameter(s) in '{config_path}': {', '.join(unknown_keys)}",
				file=sys.stderr,
			)
			sys.exit(1)

		return config_class(**config_data)

	except FileNotFoundError:
		print(f"Error: Configuration file '{config_path}' not found.", file=sys.stderr)
		sys.exit(1)
	except JSONDecodeError:
		print(f"Error: Malformed JSON in '{config_path}'.", file=sys.stderr)
		sys.exit(1)
	except TypeError as e:
		print(f"Error: Schema mismatch in '{config_path}'.\nDetails: {e}", file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"Error reading configuration file: {e}", file=sys.stderr)
		sys.exit(1)


def create_default_config(config_path: Path, config_class: type[T]) -> T:
	"""Generate, save, and return a default JSON configuration template when missing."""
	# Resolve factory method: prefers get_default classmethod if available, else standard constructor
	# using duck typing to ensure compatibility with dataclass instantiation.
	# # if it act like a duck, it can be treated as a duck. 
	factory = getattr(config_class, "get_default", config_class)
	default_config: T = factory()

	config_path.parent.mkdir(parents=True, exist_ok=True)

	try:
		with open(config_path, "w", encoding="utf-8") as f:
			dump(asdict(default_config), f, indent=4, default=str)
		print(
			f"Warning: Configuration file not found at '{config_path}'.\n"
			f"Created default template at '{config_path}'.\n",
			file=sys.stderr,
		)
	except Exception as e:
		print(
			f"Warning: Could not save default config to '{config_path}': {e}",
			file=sys.stderr,
		)

	return default_config


