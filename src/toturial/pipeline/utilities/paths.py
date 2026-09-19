from pathlib import Path

def get_project_root(marker: str = "pyproject.toml") -> Path:
	"""Find the project root by searching upwards for a marker file."""
	current = Path(__file__).resolve()
	for parent in [current] + list(current.parents):
		if (parent / marker).exists():
			return parent
	return Path.cwd()



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
