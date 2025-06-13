from discord import Member, Message, Reaction, User
from discord.ext.commands import Bot # type: ignore

from Settings import *
from src.components.group import Group
from src.components.output import Output
from src.components.requests import Requests
from src.components.vectorstore import Vectorstore
from src.translations import getLanguagePlural


async def reaction_newOrUpdateRequest(source: Reaction | Message, member: Member | User, *, requests: Requests) -> None:
	"""(Trusted event) Creates a new request for a vectorstore/permitting group addition.
	If the recipient is in the permitting group or is the requester himself/herself, the request is skipped and automatically granted."""
	sourceMessage = source.message if isinstance(source, Reaction) else source
	# Check each existing pending request whose recipient matches the message's author
	for requestMessage, requestData in ((m, r) for m, r in requests.items() if sourceMessage.author.id == r["recipientID"]):
		# Update the desired messages or requester IDs if necessary.
		dataChanged = False
		if sourceMessage not in requestData["desiredMessages"]:
			requestData["desiredMessages"].append(sourceMessage)
			dataChanged = True
		if member.id not in requestData["requesterIDs"]:
			requestData["requesterIDs"].append(member.id)
			dataChanged = True
		# If anything changed, edit the existing message
		if dataChanged:
			await Output.editWithinCharacterLimit(requestMessage, requests.populateMessage(requestData))
		break
	# Otherwise if no pending request exists for the recipient:
	else:
		requestMessages = await Output.replyWithinCharacterLimit(sourceMessage, requests.populateMessage({
			"recipientID": sourceMessage.author.id,
			"requesterIDs": [member.id],
			"desiredMessages": [sourceMessage]
		}))
		await requestMessages[-1].add_reaction("✅")
		await requestMessages[-1].add_reaction("❌")
		requests.add(requestMessages[-1], sourceMessage.author.id, [member.id], [sourceMessage])

async def reaction_requestAnswered(reaction: Reaction, yes: bool, *, requests: Requests, obj: Group | Vectorstore, bot: Bot) -> None:
	"""Handles a response to a request."""
	record = requests[reaction.message]
	if yes:
		# If the request was for a user to join permitting:
		if isinstance(obj, Group):
			if record is None: return
			if obj.add(record["recipientID"]) < 1:
				await Output.replyWithinCharacterLimit(reaction.message, "Failed to add user to group.")
			# Request message is deleted, so fall-through
		else:
			# If the request was for a user's message to be added to the vectorstore, and no record exists, it must have been self/permitting-added
			if record is None:
				if (count := obj.add(reaction.message.content, sources=reaction.message.jump_url)) < 1:
					await Output.replyWithinCharacterLimit(reaction.message, "Failed to add [count] message[plural] to the vectorstore.".replace("[count]", str(1 - count)).replace("[plural]", getLanguagePlural(LANGUAGE, 1 - count)))
					return
				if bot.user is not None:
					await reaction.message.add_reaction("✅")
					await reaction.message.remove_reaction("✅", bot.user)
				return
			# Otherwise it was an individual request that was accepted
			elif (count := obj.add((desiredMessage.content for desiredMessage in record["desiredMessages"]), sources=(desiredMessage.jump_url for desiredMessage in record["desiredMessages"]))) < len(record["desiredMessages"]):
				await Output.replyWithinCharacterLimit(reaction.message, "Failed to add [count] message[plural] to the vectorstore.".replace("[count]", str(len(record["desiredMessages"]) - count)).replace("[plural]", getLanguagePlural(LANGUAGE, len(record["desiredMessages"]) - count)))
	# Delete record of request
	if not requests.remove(reaction.message):
		await Output.replyWithinCharacterLimit(reaction.message, "Failed to delete request record.")
	# Then we delete the request message, UNLESS the request was self/permitting-added (i.e. no request message was ever sent)
	if isinstance(obj, Group) or record is not None:
		if yes: await reaction.message.add_reaction("👍")
		await reaction.message.delete(delay=1*yes)