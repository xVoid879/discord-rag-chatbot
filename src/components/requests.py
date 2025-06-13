from discord import Message
from pickle import dump, load
from typing import ItemsView, Iterable, TypedDict

from Settings import LANGUAGE
from src.components.saveableClass import SaveableClass
from src.translations import RequestsTexts

# TODO: Have requests expire and auto-delete themselves after a configurable amount of time
# TODO: Is there a way to save/load the request dictionaries (and by extension the Message objects) without resorting to possibly-vulnerable Pickle serialization/deserialization?
class RequestData(TypedDict):
	recipientID: int
	requesterIDs: list[int]
	desiredMessages: list[Message]
	
class Requests(SaveableClass):
	# Keys are request messages' IDs
	_requests: dict[Message, RequestData]
	message: str
	def __init__(self, message: str, filepath: str | None = None) -> None:
		super().__init__(filepath)
		if not message: raise ValueError(f"Invalid message provided: {message}")
		self.message = message

		if not self.load(filepath):
			self._requests = {}
	
	def __contains__(self, key: Message | int) -> bool:
		return key in self._requests if isinstance(key, Message) else any(key == entry["recipientID"] for entry in self._requests.values())
	
	def __len__(self):
		return len(self._requests)

	def items(self) -> ItemsView[Message, RequestData]:
		return self._requests.items()

	def __getitem__(self, requestMessage: Message) -> RequestData | None:
		return self._requests.get(requestMessage)

	def add(self, requestMessage: Message, recipientID: int | None = None, requesterIDs: int | Iterable[int] | None = None, desiredMessages: Message | Iterable[Message] | None = None) -> bool:
		"""Adds a new request record if one does not already exist with the provided request message ID. Otherwise, appends the provided information to the existing record."""
		# Standardize requesterIDs and desiredMessageLinks as lists
		requesterIDsList = [] if requesterIDs is None else [requesterIDs] if isinstance(requesterIDs, int) else list(set(requesterIDs))
		desiredMessagesList: list[Message] = [] if desiredMessages is None else list(set(desiredMessages)) if isinstance(desiredMessages, Iterable) else [desiredMessages]
		# If entry already exists, add new elements to existing ones
		if requestMessage in self._requests:
			# ...except for recipient ID, which is immutable
			if recipientID is not None and recipientID != self._requests[requestMessage]["recipientID"]:
				raise ValueError(RequestsTexts.RECIPIENT_ID_UNCHANGEABLE[LANGUAGE])
			self._requests[requestMessage]["requesterIDs"] += [r for r in requesterIDsList if r not in self._requests[requestMessage]["requesterIDs"]]
			self._requests[requestMessage]["desiredMessages"] += [l for l in desiredMessagesList if l not in self._requests[requestMessage]["desiredMessages"]]
		# Otherwise create a new entry
		else:
			# Recipient ID cannot be None
			if recipientID is None:
				raise ValueError(RequestsTexts.RECIPIENT_ID_MUST_EXIST[LANGUAGE])
			self._requests[requestMessage] = {
				"recipientID": recipientID,
				"requesterIDs": requesterIDsList,
				"desiredMessages": desiredMessagesList
			}
		return True

	def remove(self, requestMessage: Message) -> bool:
		if requestMessage not in self._requests: return False
		del self._requests[requestMessage]
		return True
	
	def clear(self) -> None:
		self._requests.clear()
		
	def populateMessage(self, data: RequestData) -> str:
		return self.message.replace("[recipientID]", f"<@{data['recipientID']}>").replace("[requesterIDs]", ", ".join(f"<@{requesterID}>" for requesterID in data["requesterIDs"])).replace("[desiredMessageLinks]", "\n".join(f"- {desiredMessage.jump_url}" for desiredMessage in data["desiredMessages"]))
	
	def save(self, filepath: str | None = None) -> bool:
		"""Saves the requests list to the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if (filepath := super().getFilepath(filepath)) is None: return False
		with open(filepath, "wb") as f: dump(self._requests, f)
		return True
	
	def load(self, filepath: str | None = None) -> bool:
		"""Loads the requests list from the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if (filepath := super().getFilepath(filepath)) is None: return False
		with open(filepath, "rb") as f: self._requests = load(f)
		return True