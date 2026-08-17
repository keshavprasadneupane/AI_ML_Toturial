import argparse
from dataclasses import asdict, fields
import gzip
from json import JSONDecodeError, dump, load
from pathlib import Path
import sys
from urllib import request
from urllib.parse import urlparse
import zipfile

from toturial.config_schemas import ConfigSchemas as con

DEFAULT_CONFIG_PATH = con.DEFAULT_CONFIG_DIR / "data_download.json"


def get_source_extension(url: str) -> str:
	"""Extract file extension(s) directly from the download source URL (e.g., '.gz', '.csv.gz', '.csv')."""
	url_path = urlparse(url).path
	suffixes = Path(url_path).suffixes
	return "".join(suffixes)


def get_clean_stem(file_stem: str) -> str:
	"""Ensure the stem is stripped of any accidental extension in config."""
	clean_stem = Path(file_stem).name
	while Path(clean_stem).suffix:
		clean_stem = Path(clean_stem).stem
	return clean_stem


def get_unique_path(base_path: Path) -> Path:
	"""If file exists, generate a unique path by appending a counter suffix (e.g., file_1.csv)."""
	if not base_path.exists():
		return base_path

	counter = 1
	stem = base_path.stem
	suffix = base_path.suffix
	parent = base_path.parent

	while True:
		new_path = parent / f"{stem}_{counter}{suffix}"
		if not new_path.exists():
			return new_path
		counter += 1


def read_params(config_path: Path) -> con.DataDownloadConfig:
	"""Load configuration parameters from a JSON file into DataDownloadConfig."""
	try:
		with open(config_path, "r", encoding="utf-8") as config_file:
			config = load(config_file)

		if not config or not isinstance(config, dict):
			print(
				f"Error: Configuration file '{config_path}' is empty or invalid.",
				file=sys.stderr,
			)
			sys.exit(1)

		allowed_keys = {f.name for f in fields(con.DataDownloadConfig)}
		unknown_keys = set(config.keys()) - allowed_keys
		if unknown_keys:
			print(
				f"Error: Unknown configuration parameter(s) in '{config_path}': {', '.join(unknown_keys)}",
				file=sys.stderr,
			)
			sys.exit(1)

		return con.DataDownloadConfig(**config)

	except FileNotFoundError:
		print(f"Error: Configuration file '{config_path}' not found.", file=sys.stderr)
		sys.exit(1)
	except JSONDecodeError:
		print(
			f"Error: Configuration file '{config_path}' is empty or contains malformed JSON.",
			file=sys.stderr,
		)
		sys.exit(1)
	except TypeError as e:
		print(
			f"Error: Configuration schema mismatch in '{config_path}'.\nDetails: {e}",
			file=sys.stderr,
		)
		sys.exit(1)
	except Exception as e:
		print(f"Error reading configuration file: {e}", file=sys.stderr)
		sys.exit(1)


def create_default_config(config_path: Path) -> con.DataDownloadConfig:
	"""Generate and save a default JSON configuration template when missing."""
	default_config = con.DataDownloadConfig()
	config_path.parent.mkdir(parents=True, exist_ok=True)

	data = asdict(default_config)

	try:
		with open(config_path, "w", encoding="utf-8") as f:
			dump(data, f, indent=4, default=str)
		print(
			f"Warning: Configuration file not found at '{config_path}'.\n"
			f"Created default template at '{config_path}' for future runs.\n",
			file=sys.stderr,
		)
	except Exception as e:
		print(
			f"Warning: Could not save default config to '{config_path}': {e}",
			file=sys.stderr,
		)

	return default_config


def extract_file(
	archive_path: Path,
	output_dir: Path,
	file_stem: str,
	source_ext: str,
	overwrite: bool = False,
) -> None:
	"""Extract .zip or .gz archives into target directory, checking for duplicate files."""
	print(f"Extracting {archive_path.name}...")

	if source_ext.endswith(".zip"):
		with zipfile.ZipFile(archive_path, "r") as zip_ref:
			for member in zip_ref.infolist():
				target_file = output_dir / member.filename
				if target_file.exists():
					if overwrite:
						print(
							f"Overwrite flag set (-o/--overwrite). Overwriting extracted file at {target_file}..."
						)
					else:
						new_path = get_unique_path(target_file)
						print(
							f"Extracted file '{target_file.name}' already exists. Appending counter: saving to '{new_path.name}'."
						)
						member.filename = new_path.relative_to(output_dir).as_posix()
				zip_ref.extract(member, output_dir)

	elif source_ext.endswith(".gz"):
		# Strip .gz from source_ext to get any inner extension (e.g. '.csv.gz' -> '.csv')
		inner_ext = source_ext[:-3]
		extracted_name = f"{file_stem}{inner_ext}"
		extracted_path = output_dir / extracted_name

		if extracted_path.exists():
			if overwrite:
				print(
					f"Overwrite flag set (-o/--overwrite). Overwriting existing extracted file at {extracted_path}..."
				)
			else:
				original_path = extracted_path
				extracted_path = get_unique_path(extracted_path)
				print(
					f"Extracted file '{original_path.name}' already exists. Appending counter: saving to '{extracted_path.name}'."
				)

		with gzip.open(archive_path, "rb") as f_in:
			with open(extracted_path, "wb") as f_out:
				f_out.write(f_in.read())
	else:
		print(
			f"Warning: Unsupported archive format '{source_ext}'. Skipping extraction.",
			file=sys.stderr,
		)
		return

	archive_path.unlink()
	print(f"Extraction complete. Removed archive {archive_path.name}.")


def get_data(config: con.DataDownloadConfig, overwrite: bool = False) -> None:
	"""Download data from URL and save/extract it to the specified directory."""
	save_dir = config.save_dir
	save_dir.mkdir(parents=True, exist_ok=True)

	file_stem = get_clean_stem(config.file_stem)
	source_ext = get_source_extension(config.source_url)

	target_filename = f"{file_stem}{source_ext}"
	archive_path = save_dir / target_filename

	# If NOT extracting, handle existence/counter check on the download target
	if not config.extract_archive:
		if archive_path.exists():
			if overwrite:
				print(
					f"Overwrite flag set (-o/--overwrite). Overwriting existing file at {archive_path}..."
				)
			else:
				original_path = archive_path
				archive_path = get_unique_path(archive_path)
				print(
					f"File '{original_path.name}' already exists. Appending counter: saving to '{archive_path.name}'."
				)

	print(f"Downloading data from {config.source_url}...")
	request.urlretrieve(config.source_url, archive_path)
	print(f"Data downloaded and saved to {archive_path}")

	# If extracting, handle extraction phase collision check
	if config.extract_archive:
		extract_file(
			archive_path=archive_path,
			output_dir=save_dir,
			file_stem=file_stem,
			source_ext=source_ext,
			overwrite=overwrite,
		)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Download and manage dataset configurations for ML pipeline.",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=f"""\
		Examples:
		# Run using default fallback ({DEFAULT_CONFIG_PATH}):
		python data_download.py

		# Overwrite existing files if they already exist:
		python data_download.py -o

		# Run using a specific stage config:
		python data_download.py --config configs/data_download.json
		""",
	)
	parser.add_argument(
		"-c",
		"--config",
		type=Path,
		default=None,
		help=f"Path to JSON config file (default: {DEFAULT_CONFIG_PATH}).",
	)
	parser.add_argument(
		"-o",
		"--overwrite",
		action="store_true",
		help="Overwrite the file if it already exists instead of suffixing a number.",
	)

	args = parser.parse_args()

	if args.config is not None:
		config_file_path = args.config
		if not config_file_path.exists():
			print(
				f"Error: Specified config file '{config_file_path}' does not exist.",
				file=sys.stderr,
			)
			sys.exit(1)
		config = read_params(config_file_path)
		get_data(config, overwrite=args.overwrite)
	elif DEFAULT_CONFIG_PATH.exists():
		config = read_params(DEFAULT_CONFIG_PATH)
		get_data(config, overwrite=args.overwrite)
	else:
		create_default_config(DEFAULT_CONFIG_PATH)