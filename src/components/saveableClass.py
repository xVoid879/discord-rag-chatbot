import os
from sys import argv

class SaveableClass:
	_filepath: str | None

	def __init__(self, filepath: str | None = None) -> None:
		"""Initialization."""
		if filepath is not None and (not isinstance(filepath, str) or not os.path.isfile(filepath)): raise RuntimeError(f"Invalid or nonexistent path provided: {filepath}")
		self._filepath = filepath
	
	def verify(self, proposedPath: str) -> bool:
		"""Attempts to ensure the proposed filepath will not cause damage."""
		currentDirectory = os.path.abspath(os.path.dirname(argv[0]))
		canonicalPath = os.path.abspath(proposedPath)
		return os.path.commonpath((canonicalPath, currentDirectory)).startswith(currentDirectory) and (not os.path.exists(canonicalPath) or (self._filepath is not None and os.path.samefile(proposedPath, self._filepath)))
	
	def getFilepath(self, filepath: str | None = None) -> str | None:
		"""Internally updates and returns the filepath to use, or None if no feasible filepath exists."""
		if filepath is not None and not self.verify(filepath): return None
		if not filepath:
			if not self._filepath: return None # No saved filepath exists
			filepath = self._filepath # Otherwise use saved filepath
		elif not self._filepath:
			self._filepath = filepath
		os.makedirs(os.path.dirname(filepath), exist_ok=True)
		return filepath