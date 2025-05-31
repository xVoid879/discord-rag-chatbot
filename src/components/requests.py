from discord import Message
from typing import ItemsView, Iterable, TypedDict
# from typing import Literal, TypeAlias

class RequestData(TypedDict):
	recipientID: int
	requesterIDs: list[int]
	desiredMessageLinks: list[str]

# RequestDataAttributeNames: TypeAlias = Literal["recipientID", "requesterIDs", "desiredMessageLinks"]
	
class Requests:
	# Keys are request messages' IDs
	_requests: dict[Message, RequestData]
	message: str
	# keywords: dict[str, str]
	def __init__(self, message: str, keywords: dict[str, str] | None = None) -> None:
		if not message: raise ValueError(f"Invalid message provided: {message}")
		self.message = message
		# type: ignore
		# self.keywords = {keyword: attribute for keyword, attribute in (
		# 	keywords if keywords is not None else ((f"[{attr}]", attr) for attr in RequestData.__annotations__.keys())
		# ) if keyword in message and attribute in RequestData.__annotations__.keys()}
		# if keywords is not None and len(self.keywords) < len(keywords): raise ValueError(f"Some provided keywords could not be found in provided message: {set(keywords) - set(self.keywords)}")
		
		self._requests = {}

	def __contains__(self, key: Message) -> bool:
		return key in self._requests
	
	def items(self) -> ItemsView[Message, RequestData]:
		return self._requests.items()

	def __getitem__(self, requestMessage: Message) -> RequestData | None:
		return self._requests.get(requestMessage)

	def add(self, requestMessage: Message, recipientID: int | None = None, requesterIDs: int | Iterable[int] | None = None, desiredMessageLinks: str | Iterable[str] | None = None) -> bool:
		"""Adds a new request record if one does not already exist with the provided request message ID. Otherwise, appends the provided information to the existing record."""
		# Standardize requesterIDs and desiredMessageLinks as lists
		requesterIDsList = [] if requesterIDs is None else [requesterIDs] if isinstance(requesterIDs, int) else list(set(requesterIDs))
		desiredMessageLinksList = [] if desiredMessageLinks is None else [desiredMessageLinks] if isinstance(desiredMessageLinks, str) else list(set(desiredMessageLinks))
		# If entry already exists, add new elements to existing ones
		if requestMessage in self._requests:
			# ...except for recipient ID, which is immutable
			if recipientID is not None and recipientID != self._requests[requestMessage]["recipientID"]:
				raise ValueError("Recipient ID cannot be changed.")
			self._requests[requestMessage]["requesterIDs"] += [r for r in requesterIDsList if r not in self._requests[requestMessage]["requesterIDs"]]
			self._requests[requestMessage]["desiredMessageLinks"] += [l for l in desiredMessageLinksList if l not in self._requests[requestMessage]["desiredMessageLinks"]]
		# Otherwise create a new entry
		else:
			# Recipient ID cannot be None
			if recipientID is None:
				raise ValueError("Recipient ID cannot be recorded as None.")
			self._requests[requestMessage] = {
				"recipientID": recipientID,
				"requesterIDs": requesterIDsList,
				"desiredMessageLinks": desiredMessageLinksList
			}
		return True

	def delete(self, requestMessage: Message) -> bool:
		if requestMessage not in self._requests: return False
		del self._requests[requestMessage]
		return True
		
	def populateMessage(self, data: RequestData) -> str:
		message = self.message
		# for keyword, attribute in self.keywords:
		# 	message = message.replace(keyword, str(data[attribute]))
		message = message.replace("[recipientID]", f"<@{data['recipientID']}>").replace("[requesterIDs]", ", ".join(f"<@{requesterID}>" for requesterID in data["requesterIDs"])).replace("[desiredMessageLinks]", "\n".join(f"- {messageLink}" for messageLink in data["desiredMessageLinks"]))
		return message