import os
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
		"""Adds texts to the vectorstore. Returns the number of documents added."""
		count = 0
		for mID in ([memberID] if isinstance(memberID, int) else memberID):
			self._members.add(mID)
			count += 1
		return count
	
	def remove(self, memberID: int | Iterable[int]) -> int:
		"""Removes texts from the vectorstore. Returns the number of documents removed.
		Not yet implemented."""
		count = 0
		for mID in ([memberID] if isinstance(memberID, int) else memberID):
			if mID in self._members: self._members.remove(mID)
			count += 1
		return count
	
	def __contains__(self, memberID: int) -> bool:
		return memberID in self._members
	
	def __len__(self) -> int:
		return len(self._members)
	
	def save(self, filepath: str | None = None) -> bool:
		"""Saves the group to the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
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
		if not filepath:
			if not self._filepath: return False # No saved filepath exists
			filepath = self._filepath # Otherwise use saved filepath
		if not os.path.isfile(filepath): return False
		if not self._filepath:
			self._filepath = filepath
		with open(filepath, mode="r") as f:
			self._members = {int(entry) for entry in f.readlines()}
		return True