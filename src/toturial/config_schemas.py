from dataclasses import dataclass, field
from pathlib import Path


class ConfigSchemas:
	"""
	Aggregate class for configuration parameters used in the data download process.
	"""

	DEFAULT_CONFIG_DIR: Path = Path("configs")

	@dataclass
	class DataDownloadConfig:
		"""
		Configuration parameters for downloading and saving data files.
		source_url: The URL from which to download the data file.
		save_dir: The directory where the downloaded file will be saved.
		file_stem: The base name (stem) for the saved file, without extension.
		extract_archive: Whether to extract the file if it is an archive (e.g., .zip, .tar.gz).
		"""
		source_url: str = (
			"https://raw.githubusercontent.com/dphi-official/Datasets/master/heart_disease.csv"
		)
		save_dir: Path = field(default_factory=lambda: Path("data/raw"))
		file_stem: str = "heart_disease"
		extract_archive: bool = False

		def __post_init__(self):
			# Convert string paths to Path objects if instantiated from raw JSON
			if isinstance(self.save_dir, str):
				self.save_dir = Path(self.save_dir)