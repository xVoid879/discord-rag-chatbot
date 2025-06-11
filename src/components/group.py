import os
from sys import argv
from typing import Iterable

class Group:
	_members: set[int]
	_filepath: str | None

	def __init__(self, filepath: str | None = None, initialMembers: Iterable[int] | None = None) -> None:
		"""Initialization."""
		if filepath is not None and (not isinstance(filepath, str) or not os.path.isfile(filepath)): raise RuntimeError(f"Invalid or nonexistent path provided: {filepath}")
		self._filepath = filepath

		if not self.load(filepath):
			self._members = set(initialMembers) if initialMembers is not None else set()
	
	def add(self, memberID: int | Iterable[int]) -> int:
		"""Adds texts to the group. Returns the number of users added."""
		count = 0
		for mID in ([memberID] if isinstance(memberID, int) else memberID):
			self._members.add(mID)
			count += 1
		return count
	
	def remove(self, memberID: int | Iterable[int]) -> int:
		"""Removes texts from the group. Returns the number of users removed.
		Not yet implemented."""
		count = 0
		for mID in ([memberID] if isinstance(memberID, int) else memberID):
			if mID in self._members: self._members.remove(mID)
			count += 1
		return count
	
	def clear(self) -> None:
		self._members.clear()
	
	def __contains__(self, memberID: int) -> bool:
		return memberID in self._members
	
	def __len__(self) -> int:
		return len(self._members)
	
	def save(self, filepath: str | None = None) -> bool:
		"""Saves the group to the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if filepath is not None and not self.verify(filepath): return False
		if not filepath:
			if not self._filepath: return False # No saved filepath exists
			filepath = self._filepath # Otherwise use saved filepath
		elif not self._filepath:
			self._filepath = filepath
		os.makedirs(os.path.dirname(filepath), exist_ok=True)
		with open(filepath, mode="w") as f:
			for entry in self._members:
				f.write(f"{entry}\n")
		return True
	
	def load(self, filepath: str | None = None) -> bool:
		"""Loads the group from the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if filepath is not None and not self.verify(filepath): return False
		if not filepath:
			if not self._filepath: return False # No saved filepath exists
			filepath = self._filepath # Otherwise use saved filepath
		if not os.path.isfile(filepath): return False
		if not self._filepath:
			self._filepath = filepath
		with open(filepath, mode="r") as f:
			self._members = {int(entry) for entry in f.readlines()}
		return True
	
	def verify(self, proposedPath: str) -> bool:
		"""Attempts to ensure the proposed filepath will not cause damage."""
		currentDirectory = os.path.abspath(os.path.dirname(argv[0]))
		canonicalPath = os.path.abspath(proposedPath)
		return os.path.commonpath((canonicalPath, currentDirectory)).startswith(currentDirectory) and (not os.path.exists(canonicalPath) or (self._filepath is not None and os.path.samefile(proposedPath, self._filepath)))