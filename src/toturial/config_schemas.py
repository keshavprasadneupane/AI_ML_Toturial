from dataclasses import dataclass
from pathlib import Path

class Configuration():
	"""
	Aggregate class for configuration parameters used in the data download process.
	"""
	pass
	DEFAULT_CONFIG_DIR: Path = Path("configs")


	
	@dataclass
	class DataDownloadConfig:
		data_url: str = (
			"https://raw.githubusercontent.com/dphi-official/Datasets/master/heart_disease.csv"
		)
		data_dir: Path = Path("data/raw")
		data_file: str = "heart_disease.csv"
		unzip: bool = False

		def __post_init__(self):
			# Guarantee string paths passed from JSON are converted to Path objects
			if isinstance(self.data_dir, str):
				self.data_dir = Path(self.data_dir)

