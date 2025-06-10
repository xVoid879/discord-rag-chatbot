from discord import Member, Message, Reaction, User

from Settings import *
from src.components.group import Group
from src.components.output import Output
from src.components.requests import Requests
from src.components.vectorstore import Vectorstore


async def reaction_newOrUpdateRequest(source: Reaction | Message, member: Member | User, *, requests: Requests) -> None:
	sourceMessage = source.message if isinstance(source, Reaction) else source
	# Check each existing pending request whose recipient matches the message's author
	for requestMessage, requestData in ((m, r) for m, r in requests.items() if sourceMessage.author.id == r["recipientID"]):
		# Update the desired messages or requester IDs if necessary.
		dataChanged = False
		if sourceMessage.jump_url not in requestData["desiredMessageLinks"]:
			requestData["desiredMessageLinks"].append(sourceMessage.jump_url)
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
			"desiredMessageLinks": [sourceMessage.jump_url]
		}))
		await requestMessages[-1].add_reaction("✅")
		await requestMessages[-1].add_reaction("❌")
		requests.add(requestMessages[-1], sourceMessage.author.id, [member.id], [sourceMessage.jump_url])

async def reaction_requestAnswered(reaction: Reaction, yes: bool, *, requests: Requests, obj: Group | Vectorstore) -> None:
	# await Output.replyWithinCharacterLimit(reaction.message, str(isinstance(obj, Group)))
	if yes:
		record = requests[reaction.message]
		if isinstance(obj, Group):
			if record is None: return
			if obj.add(record["recipientID"]) < 1:
				await Output.replyWithinCharacterLimit(reaction.message, "Failed to add user to group.")
		else:
			if record is None:
				if (obj.add(reaction.message.content)) < 1:
					await Output.replyWithinCharacterLimit(reaction.message, "Failed to add message to vectorstore.")
				return
			else:
				raise NotImplementedError
				# obj.add(...)
		await reaction.message.add_reaction("👍")
	if not requests.delete(reaction.message):
		await Output.replyWithinCharacterLimit(reaction.message, "Failed to delete request record.")
	await reaction.message.delete(delay=1*yes)