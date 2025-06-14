from discord import Message
from pickle import dump, load
from typing import ItemsView, Iterable, TypeAlias, TypedDict

from Settings import LANGUAGE
from src.components.group import Group
from src.components.saveableClass import SaveableClass
from src.components.vectorstore import Vectorstore
from src.translations import RequestsTexts

RequestableObjects: TypeAlias = Group | Vectorstore

# TODO: Have requests expire and auto-delete themselves after a configurable amount of time
# TODO: Is there a way to save/load the request dictionaries (and by extension the Message objects) without resorting to possibly-vulnerable Pickle serialization/deserialization?
class RequestData(TypedDict):
	recipientID: int
	requesterIDs: list[int]
	desiredMessages: list[Message]
	previousRequestMessages: list[Message]
	
class Requests(SaveableClass):
	# Keys are request messages' IDs
	_requests: dict[Message, RequestData]
	associatedObject: RequestableObjects
	message: str
	def __init__(self, associatedObject: RequestableObjects, message: str, filepath: str | None = None) -> None:
		super().__init__(filepath)
		self.associatedObject = associatedObject
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

	def add(self, requestMessage: Message, recipientID: int | None = None, requesterIDs: int | Iterable[int] | None = None, desiredMessages: Message | Iterable[Message] | None = None, previousRequestMessages: Iterable[Message] | None = None) -> bool:
		"""Adds a new request record if one does not already exist with the provided request message ID. Otherwise, appends the provided information to the existing record."""
		# Standardize requesterIDs and desiredMessageLinks as lists
		requesterIDsList = [] if requesterIDs is None else [requesterIDs] if isinstance(requesterIDs, int) else list(set(requesterIDs))
		desiredMessagesList: list[Message] = [] if desiredMessages is None else list(set(desiredMessages)) if isinstance(desiredMessages, Iterable) else [desiredMessages]
		previousRequestMessagesList = [] if previousRequestMessages is None else list(previousRequestMessages)
		# If entry already exists, add new elements to existing ones
		if requestMessage in self._requests:
			# ...except for recipient ID, which is immutable
			if recipientID is not None and recipientID != self._requests[requestMessage]["recipientID"]:
				raise ValueError(RequestsTexts.RECIPIENT_ID_UNCHANGEABLE[LANGUAGE])
			self._requests[requestMessage]["requesterIDs"] += [r for r in requesterIDsList if r not in self._requests[requestMessage]["requesterIDs"]]
			self._requests[requestMessage]["desiredMessages"] += [l for l in desiredMessagesList if l not in self._requests[requestMessage]["desiredMessages"]]
			self._requests[requestMessage]["previousRequestMessages"] += [p for p in previousRequestMessagesList if p not in self._requests[requestMessage]["previousRequestMessages"]]
		# Otherwise create a new entry
		else:
			# Recipient ID cannot be None
			if recipientID is None:
				raise ValueError(RequestsTexts.RECIPIENT_ID_MUST_EXIST[LANGUAGE])
			self._requests[requestMessage] = {
				"recipientID": recipientID,
				"requesterIDs": requesterIDsList,
				"desiredMessages": desiredMessagesList,
				"previousRequestMessages": previousRequestMessagesList
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
	
	def resolve(self, requestMessage: Message, yes: bool) -> bool:
		"""Handles a response to a request."""
		record = self._requests.get(requestMessage)
		if yes:
			# If the request was for a user to join permitting:
			if isinstance(self.associatedObject, Group):
				if record is None or self.associatedObject.add(record["recipientID"]) < 1: return False
				# Request message is deleted, so fall-through
			else:
				# If the request was for a user's message to be added to the vectorstore, and no record exists, it must have been self/permitting-added
				if record is None:
					if self.associatedObject.add(requestMessage.content, sources=requestMessage.jump_url) < 1: return False
				# Otherwise it was an individual request that was accepted
				elif self.associatedObject.add((desiredMessage.content for desiredMessage in record["desiredMessages"]), sources=(desiredMessage.jump_url for desiredMessage in record["desiredMessages"])) < len(record["desiredMessages"]): return False
		return self.remove(requestMessage)