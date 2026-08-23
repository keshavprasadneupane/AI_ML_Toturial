import argparse
import gzip
from pathlib import Path
import sys
from urllib import request
from urllib.parse import urlparse
import zipfile

from toturial.config import (
	ConfigSchemas, 
	create_default_config, 
	read_params,
	get_unique_path
)

DEFAULT_DATA_CONFIG_PATH: Path = ConfigSchemas.DEFAULT_CONFIG_DIR / "data_download.json"


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


def get_data(config: ConfigSchemas.DataDownloadConfig, overwrite: bool = False) -> None:
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

	args = parser.parse_args()

	if args.config is not None:
		config_file_path = args.config
		if not config_file_path.exists():
			print(
				f"Error: Specified config file '{config_file_path}' does not exist.",
				file=sys.stderr,
			)
			sys.exit(1)
		config = read_params(config_file_path, ConfigSchemas.DataDownloadConfig)
	elif DEFAULT_DATA_CONFIG_PATH.exists():
		config = read_params(DEFAULT_DATA_CONFIG_PATH, ConfigSchemas.DataDownloadConfig)
	else:
		config = create_default_config(DEFAULT_DATA_CONFIG_PATH, ConfigSchemas.DataDownloadConfig)
		sys.exit(0)  # Exit after creating the default config, as the user should review it before running.

	# run if not creating default config, since the program will exit after creating the default config
	get_data(config, overwrite=args.overwrite)