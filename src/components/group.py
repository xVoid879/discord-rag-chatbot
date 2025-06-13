from typing import Iterable

from src.components.saveableClass import SaveableClass

class Group(SaveableClass):
	_members: set[int]

	def __init__(self, filepath: str | None = None, initialMembers: Iterable[int] | None = None) -> None:
		"""Initialization."""
		super().__init__(filepath)

		if not self.load(filepath):
			self._members = set(initialMembers) if initialMembers is not None else set()
	
	def __len__(self):
		return len(self._members)

	def add(self, memberID: int | Iterable[int]) -> int:
		"""Adds texts to the group. Returns the number of users added."""
		count = 0
		for mID in ([memberID] if isinstance(memberID, int) else memberID):
			self._members.add(mID)
			count += 1
		return count
	
	def remove(self, memberID: int | Iterable[int]) -> int:
		"""Removes users from the group. Returns the number of users removed."""
		count = 0
		for mID in ([memberID] if isinstance(memberID, int) else memberID):
			if mID in self._members: self._members.remove(mID)
			count += 1
		return count
	
	def clear(self) -> None:
		self._members.clear()
	
	def __contains__(self, memberID: int) -> bool:
		return memberID in self._members
	
	def save(self, filepath: str | None = None) -> bool:
		"""Saves the group to the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if (filepath := super().getFilepath(filepath)) is None: return False
		with open(filepath, mode="w") as f:
			for entry in self._members:
				f.write(f"{entry}\n")
		return True
	
	def load(self, filepath: str | None = None) -> bool:
		"""Loads the group from the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if (filepath := super().getFilepath(filepath)) is None: return False
		with open(filepath, mode="r") as f:
			self._members = {int(entry) for entry in f.readlines()}
		return True