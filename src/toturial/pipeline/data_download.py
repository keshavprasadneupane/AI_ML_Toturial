import argparse
import logging
import sys
from pathlib import Path
from urllib import request
from urllib.parse import urlparse

from toturial.pipeline.config import ConfigSchemas
from toturial.pipeline.utilities import (
	Extractor ,
	create_default_config,
	get_unique_path,
	read_params,
)
from toturial.pipeline.utilities.logger import logger

CONFIG_FILE_NAME = "data_download.json"
DATA_CLEAN_DOWNLOAD_PATH_STRING = ConfigSchemas.CONFIG_DIR_NAME + f"/{CONFIG_FILE_NAME}"
DEFAULT_DATA_CONFIG_PATH: Path = ConfigSchemas.CONFIG_DIR / CONFIG_FILE_NAME


class DefaultConfigCreated(Exception):
	"""No config existed, so a default was just written — review it and re-run."""

	def __init__(self, path: Path):
		self.path = path
		super().__init__(
			f"No config file found. Created a default at '{DATA_CLEAN_DOWNLOAD_PATH_STRING}'"
			" — review it, then re-run."
		)


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


def get_data(config: ConfigSchemas.DataDownloadConfig, overwrite: bool = False) -> Path:
	"""Download data from URL and save/extract it to the specified directory."""
	save_dir = config.save_dir
	save_dir.mkdir(parents=True, exist_ok=True)

	file_stem = get_clean_stem(config.file_stem)
	source_ext = get_source_extension(config.source_url)
	archive_path = save_dir / f"{file_stem}{source_ext}"

	if not config.extract_archive and archive_path.exists():
		if overwrite:
			logger.info("Overwrite flag set (-o/--overwrite). Overwriting existing file at %s...", archive_path)
		else:
			original_name = archive_path.name
			archive_path = get_unique_path(archive_path)
			logger.info("File '%s' already exists. Appending counter: saving to '%s'.", original_name, archive_path.name)

	logger.info("Downloading data from %s...", config.source_url)
	request.urlretrieve(config.source_url, archive_path)
	logger.info("Data downloaded and saved to %s", archive_path)

	if config.extract_archive:
		Extractor.extract(
			archive_path=archive_path,
			output_dir=save_dir,
			file_stem=file_stem,
			overwrite=overwrite,
		)

	return archive_path


def load_or_resolve_config(config_path: Path | None = None) -> ConfigSchemas.DataDownloadConfig:
	if config_path is not None:
		if not config_path.exists():
			raise FileNotFoundError(f"Specified config file '{DATA_CLEAN_DOWNLOAD_PATH_STRING}' does not exist.")
		return read_params(config_path, ConfigSchemas.DataDownloadConfig)

	if DEFAULT_DATA_CONFIG_PATH.exists():
		return read_params(DEFAULT_DATA_CONFIG_PATH, ConfigSchemas.DataDownloadConfig)

	create_default_config(DEFAULT_DATA_CONFIG_PATH, ConfigSchemas.DataDownloadConfig)
	raise DefaultConfigCreated(DEFAULT_DATA_CONFIG_PATH)


def main_cli() -> None:
	parser = argparse.ArgumentParser(
		description="Download and manage dataset configurations for ML pipeline.",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=f"""\
		Examples:
		# Run using default fallback ({DEFAULT_DATA_CONFIG_PATH}):
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
		help=f"Path to JSON config file (default: {DEFAULT_DATA_CONFIG_PATH}).",
	)
	parser.add_argument(
		"-o",
		"--overwrite",
		action="store_true",
		help="Overwrite the file if it already exists instead of suffixing a number.",
	)
	parser.add_argument(
		"-v",
		"--verbose",
		action="store_true",
		help="Show INFO-level progress logging.",
	)

	args = parser.parse_args()
	logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(message)s")

	try:
		config = load_or_resolve_config(args.config)
		get_data(config, overwrite=args.overwrite)
	except DefaultConfigCreated as exc:
		print(exc, file=sys.stderr)
		sys.exit(0)
	except FileNotFoundError as exc:
		print(f"Error: {exc}", file=sys.stderr)
		sys.exit(1)
	except Exception as exc:
		print(f"Unexpected error: {exc}", file=sys.stderr)
		sys.exit(1)


if __name__ == "__main__":
	main_cli()