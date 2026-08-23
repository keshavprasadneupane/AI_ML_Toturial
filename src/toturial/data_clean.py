import argparse
from pathlib import Path
import sys
from typing import Any
import pandas as pd

from toturial.config import (
	ConfigSchemas,
	NumericDataType,
	NumericIndividualStrategy,
	NumericStrategy,
	StringStrategy,
	create_default_config,
	get_unique_path,
	read_params,
)

DEFAULT_CLEANING_CONFIG_PATH: Path = (
	ConfigSchemas.DEFAULT_CONFIG_DIR / "data_cleaning.json"
)


class ImputationResolver:
	@staticmethod
	def _safe_mode(series: pd.Series, fallback: Any = None) -> Any:
		"""Extract the first mode value safely, returning fallback if empty."""
		mode = series.mode().dropna()
		return mode.iloc[0] if not mode.empty else fallback

	@staticmethod
	def resolve_numeric_default(
		series: pd.Series,
		strategy: NumericStrategy,
		target_type: NumericDataType | None = None,
		pattern_to_remove: str | None = None,
	) -> float | int:
		"""Calculate the default imputation value for a numeric column.

		If `pattern_to_remove` is provided, the column is treated as a "special"
		column: characters matching the pattern are stripped and the result is
		coerced to `target_type` before the imputation `strategy` is applied.
		"""
		if pattern_to_remove is not None:
			series = series.astype(str).str.replace(pattern_to_remove, "", regex=True)
			match target_type:
				case NumericDataType.INTEGER | "integer":
					series = (
						pd.to_numeric(series, errors="coerce")
						.round()
						.astype("Int64")
					)
				case NumericDataType.FLOAT | "float":
					series = pd.to_numeric(series, errors="coerce")
				case _:
					raise ValueError(
						f"Unsupported target type: {target_type}. "
						f"Supported types: {NumericDataType.supported_type_string()}"
					)

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
		"""Calculate the default imputation value for a string column."""
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
		"""Resolve default imputation value for a single pandas Series."""
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
	) -> tuple[NumericStrategy, NumericDataType | None, str | None]:
		"""Resolve numeric strategy, target data type, and optional regex cleanup
		pattern for a column, following priority order:

		1. individual_numeric_strategies (covers both plain and "special"/regex
		   columns, distinguished by whether `pattern_to_remove` is set)
		2. default_numeric_strategy (no explicit dtype cast, no pattern)
		"""
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
		df: pd.DataFrame, config: ConfigSchemas.DataCleaningConfig
	) -> dict[str, float | int | str]:
		"""Resolve imputation default values for all columns in the DataFrame."""
		defaults = {}
		str_strats = config.individual_string_strategies or {}

		for col_name in df.columns:
			series = df[col_name]

			if pd.api.types.is_numeric_dtype(series):
				numeric_strat, numeric_target_type, _ = (
					ImputationResolver.resolve_numeric_config(col_name, config)
				)
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
) -> None:
	"""Clean and impute missing values in raw dataset based on configuration."""
	raw_data_path = config.data_dir / config.data_file
	cleaned_data_dir = config.cleaned_data_dir
	cleaned_data_path = cleaned_data_dir / config.cleaned_data_file

	if not raw_data_path.exists():
		print(
			f"Error: Raw data file '{raw_data_path}' does not exist.", file=sys.stderr
		)
		sys.exit(1)

	cleaned_data_dir.mkdir(parents=True, exist_ok=True)

	print(f"Loading raw data from '{raw_data_path}'...")
	df = pd.read_csv(raw_data_path)
	print(f"Columns found ({len(df.columns)}): {list(df.columns)}")

	# 1. Apply pattern removals and target conversions for any numeric column that
	# defines a regex `pattern_to_remove` (i.e. a "special" column needing cleanup
	# before type coercion / imputation).
	if config.individual_numeric_strategies:
		for col_name, strat in config.individual_numeric_strategies.items():
			pattern = (
				strat.get("pattern_to_remove")
				if isinstance(strat, dict)
				else strat.pattern_to_remove
			)
			if not pattern or col_name not in df.columns:
				continue

			target_type = (
				strat["target_type"] if isinstance(strat, dict) else strat.target_type
			)

			df[col_name] = (
				df[col_name].astype(str).str.replace(pattern, "", regex=True)
			)
			match target_type:
				case NumericDataType.INTEGER | "integer":
					df[col_name] = (
						pd.to_numeric(df[col_name], errors="coerce")
						.round()
						.astype("Int64")
					)
				case NumericDataType.FLOAT | "float":
					df[col_name] = pd.to_numeric(df[col_name], errors="coerce")

	# Track columns with pre-existing NaNs. Pandas automatically casts integer
	# columns with NaNs to float64, so this identifies potential missed integer configurations.
	cols_missing_before_impute = set(df.columns[df.isna().any()])

	# 2. Calculate missing value imputation defaults
	print("Calculating imputation values...")
	imputation_defaults = ImputationResolver.resolve_all_columns_defaults(df, config)

	# 3. Perform missing value imputation
	for col_name, default_val in imputation_defaults.items():
		if df[col_name].isna().any():
			df[col_name] = df[col_name].fillna(default_val)

	# 4. Enforce explicit integer dtypes and inform user of potential float upcasts
	for col_name in df.columns:
		if not pd.api.types.is_numeric_dtype(df[col_name]):
			continue
		_, target_type, _ = ImputationResolver.resolve_numeric_config(col_name, config)
		if target_type in (NumericDataType.INTEGER, "integer"):
			df[col_name] = (
				pd.to_numeric(df[col_name], errors="coerce").round().astype("Int64")
			)
		elif (
			pd.api.types.is_float_dtype(df[col_name])
			and col_name in cols_missing_before_impute
		):
			print(
				f"Note: '{col_name}' is float-typed and had missing values before "
				"imputation. It may be true float data or an integer column upcast by "
				"pandas due to NaNs. If it should be integer-based, add it to "
				"'individual_numeric_strategies' with an explicit 'target_type' (and "
				"'pattern_to_remove' if regex cleanup is required)."
			)

	# 5. Save cleaned dataset, appending a counter if file exists and overwrite is False
	target_path = cleaned_data_path
	if target_path.exists():
		if overwrite:
			print(
				f"Overwrite flag set (-o/--overwrite). Overwriting existing file at '{target_path}'..."
			)
		else:
			target_path = get_unique_path(target_path)
			print(
				f"File '{cleaned_data_path.name}' already exists. Appending counter: saving to '{target_path.name}'."
			)

	df.to_csv(target_path, index=False)
	print(f"Cleaned data successfully saved to '{target_path}'.")


if __name__ == "__main__":
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

	args = parser.parse_args()

	if args.config is not None:
		config_file_path = args.config
		if not config_file_path.exists():
			print(
				f"Error: Specified config file '{config_file_path}' does not exist.",
				file=sys.stderr,
			)
			sys.exit(1)
		config = read_params(config_file_path, ConfigSchemas.DataCleaningConfig)
	elif DEFAULT_CLEANING_CONFIG_PATH.exists():
		config = read_params(
			DEFAULT_CLEANING_CONFIG_PATH, ConfigSchemas.DataCleaningConfig
		)
	else:
		config = create_default_config(
			DEFAULT_CLEANING_CONFIG_PATH, ConfigSchemas.DataCleaningConfig
		)
		sys.exit(0)

	clean_data(config, overwrite=args.overwrite)