from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Self

from toturial.pipeline.utilities.paths import get_project_root


class NumericStrategy(str, Enum):
	MEAN = "mean"
	MEDIAN = "median"
	MODE = "mode"
	ZERO = "zero"

	@staticmethod
	def supported_strategy_string() -> str:
		"""Return a string representation of supported numeric strategies."""
		return ", ".join([e.value for e in NumericStrategy])


class StringStrategy(str, Enum):
	MODE = "mode"
	UNKNOWN = "unknown"

	@staticmethod	
	def supported_strategy_string() -> str:
		"""Return a string representation of supported string strategies."""
		return ", ".join([e.value for e in StringStrategy])


class NumericDataType(str, Enum):
	INTEGER = "integer"
	FLOAT = "float"

	@staticmethod
	def supported_type_string()-> str:
		"""Return a string representation of supported numeric data types."""
		return ", ".join([e.value for e in NumericDataType])


@dataclass(frozen=True)
class NumericIndividualStrategy:
	r"""Individual strategy for numeric columns, with optional regex-based cleaning.

	If `pattern_to_remove` is set, the column is treated as a "special" column:
	characters matching the pattern are stripped and the result is coerced to
	`target_type` before the imputation `strategy` is calculated (e.g. stripping units
	like "130 mmHg" -> "130"). Leave it as None for a plain numeric column that just
	needs a strategy/type applied directly.

	Attributes:
		target_type (NumericDataType): Target numeric data type.
		strategy (NumericStrategy): Imputation strategy to apply.
		pattern_to_remove (str | None): Optional regex pattern matching characters to
			strip out before type coercion (e.g., r'[^\d.]').
	"""

	target_type: NumericDataType
	strategy: NumericStrategy
	pattern_to_remove: str | None = None


class ConfigSchemas:
	CONFIG_DIR_NAME: str = "configs"
	CONFIG_DIR: Path = get_project_root() / CONFIG_DIR_NAME

	@dataclass(frozen=True)
	class DataDownloadConfig:
		source_url: str = (
			"https://raw.githubusercontent.com/dphi-official/Datasets/master/heart_disease.csv"
		)
		save_dir: Path = field(default_factory=lambda: Path("data/raw"))
		file_stem: str = "heart_disease"
		extract_archive: bool = False

		def __post_init__(self):
			if isinstance(self.save_dir, str):
				object.__setattr__(self, "save_dir", Path(self.save_dir))

		@classmethod
		def get_default(cls) -> Self:
			"""Factory method to generate the default Heart Disease download configuration."""
			return cls()

	@dataclass(frozen=True)
	class DataCleaningConfig:
		"""Configuration schema for data cleaning and imputation strategies.

		Attributes:
			data_dir (Path): Directory containing raw data files.
			data_file (str): Name of the raw input file.
			cleaned_data_dir (Path): Directory where cleaned output files are saved.
			cleaned_data_file (str): Name of the cleaned output file.
			default_numeric_strategy (NumericStrategy): Default fallback imputation strategy for numeric columns.
			default_string_strategy (StringStrategy): Default fallback imputation strategy for string columns.
			individual_numeric_strategies (dict[str, NumericIndividualStrategy] | None): Column-specific
				numeric overrides. Set `pattern_to_remove` on an entry to treat it as a "special" column
				requiring regex cleanup and type coercion before imputation.
			individual_string_strategies (dict[str, StringStrategy] | None): Column-specific string overrides.
		"""

		data_dir: Path = field(default_factory=lambda: Path("data/raw"))
		data_file: str = "dataset.csv"
		cleaned_data_dir: Path = field(default_factory=lambda: Path("data/cleaned"))
		cleaned_data_file: str = "dataset_cleaned.csv"
		default_numeric_strategy: NumericStrategy = NumericStrategy.MEAN
		default_string_strategy: StringStrategy = StringStrategy.MODE

		# Optional strategy overrides (default to None / null in JSON)
		individual_numeric_strategies: dict[str, NumericIndividualStrategy] | None = None
		individual_string_strategies: dict[str, StringStrategy] | None = None

		def __post_init__(self):
			if isinstance(self.data_dir, str):
				object.__setattr__(self, "data_dir", Path(self.data_dir))
			if isinstance(self.cleaned_data_dir, str):
				object.__setattr__(
					self, "cleaned_data_dir", Path(self.cleaned_data_dir)
				)

			# Reconstruct numeric strategies if loaded as dicts from JSON
			if self.individual_numeric_strategies:
				reconstructed_num = {}
				for col, strat in self.individual_numeric_strategies.items():
					if isinstance(strat, dict):
						reconstructed_num[col] = NumericIndividualStrategy(
							target_type=NumericDataType(strat["target_type"]),
							strategy=NumericStrategy(strat["strategy"]),
							pattern_to_remove=strat.get("pattern_to_remove"),
						)
					else:
						reconstructed_num[col] = strat
				object.__setattr__(
					self, "individual_numeric_strategies", reconstructed_num
				)

			# Reconstruct string strategies if loaded as raw strings from JSON
			if self.individual_string_strategies:
				reconstructed_str = {}
				for col, strat in self.individual_string_strategies.items():
					if isinstance(strat, str):
						reconstructed_str[col] = StringStrategy(strat)
					else:
						reconstructed_str[col] = strat
				object.__setattr__(
					self, "individual_string_strategies", reconstructed_str
				)

		@classmethod
		def get_default(cls) -> Self:
			"""Factory method to generate the default Heart Disease cleaning configuration."""
			return cls(
				data_file="heart_disease.csv",
				cleaned_data_file="heart_disease_cleaned.csv",
				individual_numeric_strategies={
					"trestbps": NumericIndividualStrategy(
						target_type=NumericDataType.INTEGER,
						strategy=NumericStrategy.MEAN,
					),
					"chol": NumericIndividualStrategy(
						target_type=NumericDataType.INTEGER,
						strategy=NumericStrategy.MEAN,
					),
					"thalach": NumericIndividualStrategy(
						target_type=NumericDataType.INTEGER,
						strategy=NumericStrategy.MEAN,
					),
					"oldpeak": NumericIndividualStrategy(
						target_type=NumericDataType.INTEGER,
						strategy=NumericStrategy.MEDIAN,
						pattern_to_remove=r"[^\d.]",
					),
					"ca": NumericIndividualStrategy(
						target_type=NumericDataType.INTEGER,
						strategy=NumericStrategy.MODE,
						pattern_to_remove=r"[^\d]",
					),
				},
				individual_string_strategies={
					"thal": StringStrategy.MODE,
					"cp": StringStrategy.MODE,
				},
			)