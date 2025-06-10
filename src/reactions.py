from discord import Member, Reaction

from Settings import *
from src.components.output import Output
from src.components.requests import Requests
from src.components.vectorstore import Vectorstore


async def reaction_newOrUpdateRequest(reaction: Reaction, member: Member, *, requests: Requests) -> None:
	# Check each existing pending request whose recipient matches the message's author
	for requestMessage, requestData in ((m, r) for m, r in requests.items() if reaction.message.author.id == r["recipientID"]):
		# Update the desired messages or requester IDs if necessary.
		dataChanged = False
		if reaction.message.jump_url not in requestData["desiredMessageLinks"]:
			requestData["desiredMessageLinks"].append(reaction.message.jump_url)
			dataChanged = True
		if member.id not in requestData["requesterIDs"]:
			requestData["requesterIDs"].append(member.id)
			# 3142285341
			dataChanged = True
		# If anything changed, edit the existing message
		if dataChanged:
			await Output.editWithinCharacterLimit(requestMessage, requests.populateMessage(requestData))
		break
	# Otherwise if no pending request exists for the recipient:
	else:
		requestMessages = await Output.replyWithinCharacterLimit(reaction.message, requests.populateMessage({
			"recipientID": reaction.message.author.id,
			"requesterIDs": [member.id],
			"desiredMessageLinks": [reaction.message.jump_url]
		}))
		await requestMessages[-1].add_reaction("✅")
		await requestMessages[-1].add_reaction("❌")
		requests.add(requestMessages[-1], reaction.message.author.id, [member.id], [reaction.message.jump_url])

async def reaction_requestAnswered(reaction: Reaction, member: Member, yes: bool, *, requests: Requests, vectorstore: Vectorstore) -> None:
	raise NotImplementedError
	# if reaction.emoji == "✅":
	# 	vectorstore.add(...)
	# requests.delete()