from pathlib import Path
import libarchive
import numpy as np
from .paths import get_unique_path
from .logger import logger


class Extractor:
	"""Dispatches archive files to the appropriate extraction engine."""
	@staticmethod
	def extract(archive_path: Path, output_dir: Path, file_stem: str, overwrite: bool = False) -> None:
		"""Extracts any supported archive type into target directory."""
		output_dir.mkdir(parents=True, exist_ok=True)
		# 1. Universal libarchive-c handler (ZIP, TAR, 7z, ISO, GZ, BZ2, XZ, etc.)
		try:
			Extractor._extract_libarchive(archive_path, output_dir, file_stem, overwrite)
		except libarchive.ArchiveError as err:
			logger.error("Failed to extract %s via libarchive: %s", archive_path.name, err)
			raise

	@staticmethod
	def _extract_numpy(archive_path: Path, output_dir: Path, file_stem: str, overwrite: bool) -> None:
		"""Handles NumPy array archives and binary dumps."""
		logger.info("Extracting NumPy file %s...", archive_path.name)
		data = np.load(archive_path)

		if hasattr(data, "files"):
			# Multi-array .npz archive
			for key in data.files:
				target_file = output_dir / f"{file_stem}_{key}.npy"
				if target_file.exists() and not overwrite:
					target_file = get_unique_path(target_file)
				np.save(target_file, data[key])
				logger.info("Saved array '%s' -> %s", key, target_file.name)
		else:
			# Single .npy binary dump
			target_file = output_dir / f"{file_stem}.npy"
			if target_file.exists() and not overwrite:
				target_file = get_unique_path(target_file)
			np.save(target_file, data)
			logger.info("Saved NumPy array -> %s", target_file.name)

		archive_path.unlink()

	@staticmethod
	def _extract_libarchive(archive_path: Path, output_dir: Path, file_stem: str, overwrite: bool) -> None:
		"""Handles standard compressed archives and raw streams without extension checking."""
		logger.info("Extracting archive %s...", archive_path.name)

		with libarchive.file_reader(str(archive_path)) as archive:
			for entry in archive:
				# If entry doesn't have an internal filename (e.g. standard raw gzip stream), fall back to stem
				target_name = entry.pathname if entry.pathname else file_stem
				target_file = output_dir / target_name

				# Prevent Path traversal security flaws (Zip Slip)
				resolved_target = target_file.resolve()
				if not resolved_target.is_relative_to(output_dir.resolve()):
					logger.warning("Skipping unsafe path traversal entry: %s", entry.pathname)
					continue

				if entry.isdir:
					target_file.mkdir(parents=True, exist_ok=True)
					continue

				target_file.parent.mkdir(parents=True, exist_ok=True)

				if target_file.exists():
					if overwrite:
						logger.info("Overwrite active: replacing %s", target_file)
					else:
						new_path = get_unique_path(target_file)
						logger.info("File '%s' exists. Saving to '%s'.", target_file.name, new_path.name)
						target_file = new_path

				with open(target_file, "wb") as f_out:
					for block in entry.get_blocks():
						f_out.write(block)

		archive_path.unlink()
		logger.info("Successfully extracted and removed %s.", archive_path.name)