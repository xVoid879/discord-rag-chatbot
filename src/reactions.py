from discord import Interaction, Member, Message, Reaction, User
from discord.ext.commands import Bot # type: ignore
from typing import overload

from Settings import *
from src.components.group import Group
from src.components.output import Output
from src.components.requests import Requests

# TODO: Migrate to requests.py

@overload
async def reaction_newOrUpdateRequest(source: Reaction | Message, requestingMessageOrUser: Interaction | Message, *, requests: Requests) -> None:
	raise NotImplementedError

@overload
async def reaction_newOrUpdateRequest(source: Reaction | Message, requestingMessageOrUser: Member | User, *, requests: Requests) -> None:
	raise NotImplementedError

async def reaction_newOrUpdateRequest(source: Reaction | Message, requestingMessageOrUser: Interaction | Message | Member | User, *, requests: Requests) -> None:
	"""(Trusted event) Creates a new request for a vectorstore/permitting group addition."""
	desiredMessage = source.message if isinstance(source, Reaction) else source
	requester = requestingMessageOrUser.user if isinstance(requestingMessageOrUser, Interaction) else requestingMessageOrUser if isinstance(requestingMessageOrUser, (Member, User)) else requestingMessageOrUser.author
	# Check each existing pending request whose recipient matches the message's author
	for requestMessage, requestData in ((m, d) for m, d in requests.items() if desiredMessage.author.id == d["recipientID"]):
		# Update the desired messages or requester IDs if necessary.
		dataChanged = False
		if desiredMessage not in requestData["desiredMessages"]:
			requestData["desiredMessages"].append(desiredMessage)
			dataChanged = True
		if requester.id not in requestData["requesterIDs"]:
			requestData["requesterIDs"].append(requester.id)
			dataChanged = True
		# If anything changed, edit the existing message
		if dataChanged:
			await Output.editWithinCharacterLimit(requestMessage, requests.populateMessage(requestData))
		break
	# Otherwise if no pending request exists for the recipient:
	else:
		requestMessages = await Output.replyWithinCharacterLimit(requestingMessageOrUser if isinstance(requestingMessageOrUser, (Interaction, Message)) else desiredMessage, requests.populateMessage({
			"recipientID": desiredMessage.author.id,
			"requesterIDs": [requester.id],
			"desiredMessages": [desiredMessage],
			"previousRequestMessages": []
		}))
		await requestMessages[-1].add_reaction("✅")
		await requestMessages[-1].add_reaction("❌")
		requests.add(requestMessages[-1], desiredMessage.author.id, [requester.id], [desiredMessage], requestMessages[:-1])

async def reaction_answerRequest(source: Message | Reaction, yes: bool, *, requests: Requests, bot: Bot) -> None:
	"""Handles a response to a request."""
	sourceMessage = source.message if isinstance(source, Reaction) else source
	# We should ultimately delete the request message UNLESS the request was self/permitting-added (i.e. no request message was ever sent)
	messagesToDelete = ([sourceMessage] if isinstance(requests.associatedObject, Group) or sourceMessage in requests else []) + (record["previousRequestMessages"] if (record := requests[sourceMessage]) is not None else [])
	if not requests.resolve(sourceMessage, yes): return await Output.indicateFailure(sourceMessage)
	# Indicate success, then delete all relevant messages (or simply remove reaction if no messages should be deleted)
	if yes: await sourceMessage.add_reaction("👍")
	if messagesToDelete:
		# Only wait on the last message and if the answer was yes (so user can see the thumbs-up)
		for message in messagesToDelete: await message.delete(delay=0.75*yes*(message == sourceMessage))
	elif yes and bot.user is not None: await sourceMessage.remove_reaction("👍", bot.user)