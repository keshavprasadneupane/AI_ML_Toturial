import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from toturial.pipeline.config import (
	ConfigSchemas,
	NumericDataType,
	NumericIndividualStrategy,
	NumericStrategy,
	StringStrategy,
)
from toturial.pipeline.utilities import(
	get_unique_path, read_params, create_default_config
)

from toturial.pipeline.utilities.logger import logger

CONFIG_FILE_NAME = "data_cleaning.json"
DATA_CLEAN_CONFIG_PATH_STRING = ConfigSchemas.CONFIG_DIR_NAME + f"/{CONFIG_FILE_NAME}"
DEFAULT_CLEANING_CONFIG_PATH: Path = ConfigSchemas.CONFIG_DIR / CONFIG_FILE_NAME



NumericColumnConfig = tuple[NumericStrategy, "NumericDataType | None", "str | None"]


class DefaultConfigCreated(Exception):
	"""Raised when no config file existed, so a fresh default was written.

	This isn't a failure — it's a signal to the caller that first-run setup
	just happened and the user should review the generated file before
	re-running. Kept as an exception so library callers can catch and handle
	it however they want.
	"""

	def __init__(self, path: Path):
		self.path = path
		super().__init__(
			f"No config file found. A default one has been created at "
			f"'{DATA_CLEAN_CONFIG_PATH_STRING}'. Review and edit it, then re-run."
		)


class ImputationResolver:
	@staticmethod
	def _safe_mode(series: pd.Series, fallback: Any = None) -> Any:
		mode = series.mode().dropna()
		return mode.iloc[0] if not mode.empty else fallback

	@staticmethod
	def cast_to_target_type(
		series: pd.Series, target_type: "NumericDataType | str"
	) -> pd.Series:
		match target_type:
			case NumericDataType.INTEGER | "integer":
				return pd.to_numeric(series, errors="coerce").round().astype("Int64")
			case NumericDataType.FLOAT | "float":
				return pd.to_numeric(series, errors="coerce")
			case _:
				raise ValueError(
					f"Unsupported target type: {target_type}. "
					f"Supported types: {NumericDataType.supported_type_string()}"
				)

	@staticmethod
	def resolve_numeric_default(
		series: pd.Series,
		strategy: NumericStrategy,
		target_type: NumericDataType | None = None,
		pattern_to_remove: str | None = None,
	) -> float | int:
		if pattern_to_remove is not None:
			series = series.astype(str).str.replace(pattern_to_remove, "", regex=True)
			if target_type is None:
				raise ValueError(
					"pattern_to_remove was set but no target_type was given — "
					"can't tell whether to coerce to int or float."
				)
			series = ImputationResolver.cast_to_target_type(series, target_type)

		match strategy:
			case NumericStrategy.MEAN:
				val = series.mean()
			case NumericStrategy.MEDIAN:
				val = series.median()
			case NumericStrategy.MODE:
				val = ImputationResolver._safe_mode(series, fallback=0)
			case NumericStrategy.ZERO:
				val = 0
			case _:
				raise ValueError(
					f"Unsupported numeric strategy: {strategy}. "
					f"Supported strategies: {NumericStrategy.supported_strategy_string()}"
				)

		if pd.isna(val) or val is None:
			val = 0

		if target_type == NumericDataType.INTEGER:
			return int(round(float(val)))

		return float(val)

	@staticmethod
	def resolve_string_default(series: pd.Series, strategy: StringStrategy) -> str:
		match strategy:
			case StringStrategy.MODE:
				val = ImputationResolver._safe_mode(
					series, fallback=StringStrategy.UNKNOWN
				)
				return str(val)
			case StringStrategy.UNKNOWN:
				return StringStrategy.UNKNOWN
			case _:
				raise ValueError(
					f"Unsupported string strategy: {strategy}. "
					f"Supported strategies: {StringStrategy.supported_strategy_string()}"
				)

	@staticmethod
	def resolve_column_default(
		series: pd.Series,
		numeric_strategy: NumericStrategy = NumericStrategy.MEAN,
		string_strategy: StringStrategy = StringStrategy.MODE,
		numeric_target_type: NumericDataType | None = None,
		pattern_to_remove: str | None = None,
	) -> float | int | str:
		"""Resolve a single column's imputation default in isolation.

		Not called anywhere in this module's own pipeline (``clean_data`` resolves
		every column via ``resolve_all_columns_defaults`` instead) — kept as a
		standalone entry point in case other code imports ``ImputationResolver``
		directly for one-off columns.
		"""
		if pattern_to_remove is not None:
			return ImputationResolver.resolve_numeric_default(
				series=series,
				strategy=numeric_strategy,
				target_type=numeric_target_type,
				pattern_to_remove=pattern_to_remove,
			)

		if pd.api.types.is_numeric_dtype(series):
			return ImputationResolver.resolve_numeric_default(
				series=series,
				strategy=numeric_strategy,
				target_type=numeric_target_type,
			)
		elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(
			series
		):
			return ImputationResolver.resolve_string_default(series, string_strategy)
		else:
			raise ValueError(
				f"Unsupported data type '{series.dtype}' for column '{series.name}'."
				" Supported types: numeric, string/object."
			)

	@staticmethod
	def resolve_numeric_config(
		col_name: str, config: ConfigSchemas.DataCleaningConfig
	) -> NumericColumnConfig:
		num_strats = config.individual_numeric_strategies or {}
		ind_num = num_strats.get(col_name)

		if isinstance(ind_num, NumericIndividualStrategy):
			return ind_num.strategy, ind_num.target_type, ind_num.pattern_to_remove
		if isinstance(ind_num, NumericStrategy):
			return ind_num, None, None
		if isinstance(ind_num, str):
			return NumericStrategy(ind_num), None, None
		if isinstance(ind_num, dict):
			strategy = NumericStrategy(ind_num["strategy"])
			target_type = (
				NumericDataType(ind_num["target_type"])
				if ind_num.get("target_type")
				else None
			)
			pattern_to_remove = ind_num.get("pattern_to_remove")
			return strategy, target_type, pattern_to_remove

		return config.default_numeric_strategy, None, None

	@staticmethod
	def resolve_all_columns_defaults(
		df: pd.DataFrame,
		config: ConfigSchemas.DataCleaningConfig,
		numeric_configs: dict[str, NumericColumnConfig] | None = None,
	) -> dict[str, float | int | str]:
		"""
		Resolve imputation defaults for all columns in the DataFrame, using the provided
		cleaning configuration. Returns a dictionary mapping column names to their
		resolved default values.
		"""
		defaults = {}
		str_strats = config.individual_string_strategies or {}
		numeric_configs = numeric_configs or {}

		for col_name in df.columns:
			series = df[col_name]

			if pd.api.types.is_numeric_dtype(series):
				numeric_strat, numeric_target_type, _ = numeric_configs.get(
					col_name
				) or ImputationResolver.resolve_numeric_config(col_name, config)
				defaults[col_name] = ImputationResolver.resolve_numeric_default(
					series=series,
					strategy=numeric_strat,
					target_type=numeric_target_type,
				)
			elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(
				series
			):
				ind_str = str_strats.get(col_name)
				if isinstance(ind_str, StringStrategy):
					string_strat = ind_str
				elif isinstance(ind_str, str):
					string_strat = StringStrategy(ind_str)
				else:
					string_strat = config.default_string_strategy
				defaults[col_name] = ImputationResolver.resolve_string_default(
					series, string_strat
				)
			else:
				raise ValueError(
					f"Unsupported data type '{series.dtype}' for column '{col_name}'."
					" Supported types: numeric, string/object."
				)

		return defaults


def clean_data(
	config: ConfigSchemas.DataCleaningConfig, overwrite: bool = False
) -> Path:
	"""Load, clean, and save the configured data file. Returns the output path.

	Raises ``FileNotFoundError`` if the raw data file is missing — it's on the
	caller (``main_cli``) to decide what that means for the process exit code.
	"""
	raw_data_path = config.data_dir / config.data_file
	cleaned_data_dir = config.cleaned_data_dir
	cleaned_data_path = cleaned_data_dir / config.cleaned_data_file

	if not raw_data_path.exists():
		raise FileNotFoundError(
			f"Raw data file '{DATA_CLEAN_CONFIG_PATH_STRING}' does not exist."
		)

	cleaned_data_dir.mkdir(parents=True, exist_ok=True)

	logger.info("Loading raw data from '%s'...", raw_data_path)
	df = pd.read_csv(raw_data_path)
	logger.info("Columns found (%d): %s", len(df.columns), list(df.columns))
	logger.info("Missing values per column:\n%s", df.isna().sum())

	# Resolve every numeric column's (strategy, target_type, pattern) tuple once,
	# up front, and reuse it for pattern-stripping, imputation, and the post-cast
	# pass below — instead of re-deriving it three separate times.
	numeric_configs: dict[str, NumericColumnConfig] = {
		col_name: ImputationResolver.resolve_numeric_config(col_name, config)
		for col_name in df.columns
		if pd.api.types.is_numeric_dtype(df[col_name])
		or col_name in (config.individual_numeric_strategies or {})
	}

	for col_name, (_, target_type, pattern) in numeric_configs.items():
		if not pattern or col_name not in df.columns:
			continue
		if target_type is None:
			raise ValueError(
				f"Column '{col_name}' has a pattern_to_remove but no target_type "
				"— add one so cleaned values can be cast correctly."
			)
		df[col_name] = df[col_name].astype(str).str.replace(pattern, "", regex=True)
		df[col_name] = ImputationResolver.cast_to_target_type(
			df[col_name], target_type
		)

	cols_missing_before_impute = set(df.columns[df.isna().any()])

	logger.info("Calculating imputation values...")
	imputation_defaults = ImputationResolver.resolve_all_columns_defaults(
		df, config, numeric_configs
	)

	for col_name, default_val in imputation_defaults.items():
		if df[col_name].isna().any():
			df[col_name] = df[col_name].fillna(default_val)

	for col_name, (_, target_type, _) in numeric_configs.items():
		if col_name not in df.columns or not pd.api.types.is_numeric_dtype(
			df[col_name]
		):
			continue
		if target_type in (NumericDataType.INTEGER, "integer"):
			df[col_name] = ImputationResolver.cast_to_target_type(
				df[col_name], target_type
			)
		elif (
			pd.api.types.is_float_dtype(df[col_name])
			and col_name in cols_missing_before_impute
		):
			logger.warning(
				"'%s' is float-typed and had missing values before imputation. "
				"It may be true float data or an integer column upcast by pandas "
				"due to NaNs. If it should be integer-based, add it to "
				"'individual_numeric_strategies' with an explicit target_type "
				"(and pattern_to_remove if regex cleanup is required).",
				col_name,
			)

	target_path = cleaned_data_path
	if target_path.exists():
		if overwrite:
			logger.info(
				"Overwrite flag set (-o/--overwrite). Overwriting existing file "
				"at '%s'...",
				target_path,
			)
		else:
			target_path = get_unique_path(target_path)
			logger.info(
				"File '%s' already exists. Appending counter: saving to '%s'.",
				cleaned_data_path.name,
				target_path.name,
			)

	df.to_csv(target_path, index=False)
	logger.info("Cleaned data successfully saved to '%s'.", target_path)
	return target_path


def load_or_resolve_config(
	config: ConfigSchemas.DataCleaningConfig | dict | None = None,
	config_path: Path | str | None = None,
) -> ConfigSchemas.DataCleaningConfig:
	"""
	Load a data cleaning config from a JSON file, or create a default one if none exists.
	Raises ``DefaultConfigCreated`` if a default config was created, so the caller can
	decide how to handle it (e.g., exit with a message).
	"""
	if config is not None:
		if isinstance(config, ConfigSchemas.DataCleaningConfig):
			return config
		if isinstance(config, dict):
			return ConfigSchemas.DataCleaningConfig(**config)

	path = Path(config_path) if config_path else DEFAULT_CLEANING_CONFIG_PATH

	if config_path is not None and not path.exists():
		raise FileNotFoundError(
			f"Specified config file '{DATA_CLEAN_CONFIG_PATH_STRING}' does not exist."
		)

	if path.exists():
		return read_params(path, ConfigSchemas.DataCleaningConfig)

	create_default_config(path, ConfigSchemas.DataCleaningConfig)
	raise DefaultConfigCreated(path)


def data_cleaning_main(
	config: ConfigSchemas.DataCleaningConfig | dict | None = None,
	config_path: Path | str | None = None,
	overwrite: bool = False,
) -> Path:
	resolved_config = load_or_resolve_config(config=config, config_path=config_path)
	return clean_data(resolved_config, overwrite=overwrite)


def main_cli() -> None:
	parser = argparse.ArgumentParser(
		description="Cleans the downloaded data based on the provided configuration.",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=f"""\
		Examples:
		# Run using default configuration ({DEFAULT_CLEANING_CONFIG_PATH}):
		python data_clean.py

		# Overwrite existing files:
		python data_clean.py -o

		# Run with custom config file:
		python data_clean.py --config configs/data_cleaning.json
		""",
	)
	parser.add_argument(
		"-c",
		"--config",
		type=Path,
		default=None,
		help=f"Path to JSON config file (default: {DEFAULT_CLEANING_CONFIG_PATH}).",
	)
	parser.add_argument(
		"-o",
		"--overwrite",
		action="store_true",
		help="Overwrite output file if it already exists.",
	)
	parser.add_argument(
		"-v",
		"--verbose",
		action="store_true",
		help="Show INFO-level progress logging.",
	)

	args = parser.parse_args()
	logging.basicConfig(
		level=logging.INFO if args.verbose else logging.WARNING,
		format="%(message)s",
	)

	# This is the one place in the whole module allowed to call sys.exit — every
	# other function raises instead, so the exit code and error message are both
	# decided right here, next to the argparse setup, rather than scattered
	# through the business logic.
	try:
		data_cleaning_main(config_path=args.config, overwrite=args.overwrite)
	except DefaultConfigCreated as exc:
		print(exc, file=sys.stderr)
		sys.exit(0)
	except FileNotFoundError as exc:
		print(f"Error: {exc}", file=sys.stderr)
		sys.exit(1)
	except (ValueError, KeyError) as exc:
		print(f"Error: Invalid configuration or data — {exc}", file=sys.stderr)
		sys.exit(1)
	except Exception as exc:  # noqa: BLE001 - CLI boundary: never leak a raw traceback
		print(f"Unexpected error: {exc}", file=sys.stderr)
		sys.exit(1)


if __name__ == "__main__":
	main_cli()