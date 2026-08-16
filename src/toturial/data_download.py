import argparse
from dataclasses import asdict, fields
import gzip
from json import JSONDecodeError, dump, load
from pathlib import Path
import sys
from urllib import request
import zipfile

from toturial.config_schemas import Configuration as con

DEFAULT_CONFIG_PATH = con.DEFAULT_CONFIG_DIR / "data_download.json"


def read_params(config_path: Path) -> con.DataDownloadConfig:
    """Load configuration parameters from a JSON file into DataDownloadConfig."""
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = load(config_file)

        if not config or not isinstance(config, dict):
            print(f"Error: Configuration file '{config_path}' is empty or invalid.", file=sys.stderr)
            sys.exit(1)

        # Detect unknown fields in the JSON file
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
        print(f"Error: Configuration file '{config_path}' is empty or contains malformed JSON.", file=sys.stderr)
        sys.exit(1)
    except TypeError as e:
        print(f"Error: Configuration schema mismatch in '{config_path}'.\nDetails: {e}", file=sys.stderr)
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
        print(f"Warning: Could not save default config to '{config_path}': {e}", file=sys.stderr)

    return default_config


def extract_file(file_path: Path, output_dir: Path) -> None:
    """Extract .zip or .gz archives into the target directory."""
    print(f"Extracting {file_path.name}...")

    if file_path.suffix == ".zip":
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)
    elif file_path.suffix == ".gz":
        extracted_path = output_dir / file_path.stem
        with gzip.open(file_path, "rb") as f_in:
            with open(extracted_path, "wb") as f_out:
                f_out.write(f_in.read())
    else:
        print(f"Warning: Unsupported archive format '{file_path.suffix}'. Skipping extraction.", file=sys.stderr)
        return

    file_path.unlink()
    print(f"Extraction complete. Removed archive {file_path.name}.")


def get_data(config: con.DataDownloadConfig) -> None:
    """Download data from URL and save/extract it to the specified directory."""
    data_dir = config.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / config.data_file

    if not data_path.exists():
        print(f"Downloading data from {config.data_url}...")
        request.urlretrieve(config.data_url, data_path)
        print(f"Data downloaded and saved to {data_path}")

        if config.unzip:
            extract_file(data_path, data_dir)
    else:
        print(f"Data already exists at {data_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and manage dataset configurations for ML pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""\
Examples:
  # Run using default fallback ({DEFAULT_CONFIG_PATH}):
  python data_download.py

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

    args = parser.parse_args()

    if args.config is not None:
        config_file_path = args.config
        if not config_file_path.exists():
            print(f"Error: Specified config file '{config_file_path}' does not exist.", file=sys.stderr)
            sys.exit(1)
        config = read_params(config_file_path)
    elif DEFAULT_CONFIG_PATH.exists():
        config = read_params(DEFAULT_CONFIG_PATH)
    else:
        config = create_default_config(DEFAULT_CONFIG_PATH)

    get_data(config)