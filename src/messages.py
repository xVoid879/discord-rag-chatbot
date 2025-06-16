from discord import Interaction, Message
from discord.ext.commands import Bot # type: ignore
from itertools import repeat
from typing import Iterable

from Settings import *
from src.components.ai import AI
from src.components.cache import Cache
from src.components.cooldown import Cooldown
from src.components.group import Group
from src.components.discord import Discord
from src.components.requests import Requests
from src.components.vectorstore import Vectorstore
from Translations import MessagesTexts, getLanguagePlural


async def message_add(source: Interaction | Message, *entries: str, obj: Group) -> None:
	"""(Trusted command) Adds the specified entry to the specified object."""
	# Temporary
	savedCount = 0
	if isinstance(obj, Group):
		savedCount = obj.add([int(entry.strip("<@!> ")) for entry in entries])

	if savedCount < len(entries):
		return await Discord.indicateFailure(source, MessagesTexts.ADD__ERROR[LANGUAGE].replace("[count]", f"{len(entries) - savedCount}").replace("[plural]", getLanguagePlural(LANGUAGE, len(entries) - savedCount)))
	await Discord.indicateSuccess(source)


async def message_ask(
	source: Interaction | Message,
	query: str,
	*,
	ai: AI | None = None,
	cache: Cache | None = None,
	cooldown: Cooldown | None = None,
	vectorstore: Vectorstore | None = None
) -> None:
	"""Generate an answer to the provided query, subject to a cooldown."""
	# Check cooldown
	if cooldown is not None:
		if (remainingCooldown := cooldown.getRemainingTime()) > 0.:
			return await Discord.indicateFailure(source, MessagesTexts.ASK__COOLDOWN[LANGUAGE].replace("[seconds]", f"{remainingCooldown:.2g}"))
	# Check cache
	if cache is not None:
		if response := cache.getExactMatch(query):
			await Discord.replyWithinCharacterLimit(source, response + "\n-# " + MessagesTexts.ASK__CACHED_RESPONSE[LANGUAGE] + (" " + MessagesTexts.ASK__AI_DISCLAIMER[LANGUAGE] if ai is not None else ""))
			return
		if response := cache.getSemanticMatch(query):
			await Discord.replyWithinCharacterLimit(source, response + "\n-# " + MessagesTexts.ASK__CACHED_RESPONSE[LANGUAGE] + (" " + MessagesTexts.ASK__AI_DISCLAIMER[LANGUAGE] if ai is not None else ""))
			return
	# Retrieve context and scores from vectorstore
	context = "\n\n".join(f"{'' if ai is not None else (sourceURL if sourceURL is not None else '[' + MessagesTexts.ASK__DEFAULT_SOURCE[LANGUAGE] + ']') + ' '}_({MessagesTexts.ASK__RELEVANCE_ESTIMATE[LANGUAGE].replace('[relevance]', f'**{score:.2%}**')})_\n{text}".strip() for text, sourceURL, score in vectorstore.query(query)) if vectorstore is not None else MessagesTexts.ASK__DEFAULT_CONTEXT[LANGUAGE]
	if context and context != MessagesTexts.ASK__DEFAULT_CONTEXT[LANGUAGE]:
		context = "\n" + context
	# If context is required, and no context is found, return error
	elif AI_REQUIRE_CONTEXT:
		await Discord.replyWithinCharacterLimit(source, MessagesTexts.ASK__ERROR_IF_NO_CONTEXT[LANGUAGE])
		return

	# Retrieve AI response
	# TODO: Automatically truncate number of context messages returned if AI is disabled but max AI output characters is specified
	response = ai.query(query, context) if ai is not None else MessagesTexts.ASK__RETURN_VECTORSTORE[LANGUAGE].replace("[messages]", context)
	# Send message to user, and cache for future
	await Discord.replyWithinCharacterLimit(source, response + ("\n-# " + MessagesTexts.ASK__AI_DISCLAIMER[LANGUAGE] if ai is not None else ""))
	if cache is not None:
		cache[query] = (response, cache.embed(query))


async def message_clear(source: Interaction | Message, *, objects: Iterable[Cache | Group | Requests | Vectorstore]) -> None:
	"""(Trusted command) Clears the specified object."""
	for obj in objects: obj.clear()
	await Discord.indicateSuccess(source)


async def message_help(source: Interaction | Message, command: str | None = None) -> None:
	"""Prints the help message."""
	await Discord.replyWithinCharacterLimit(source, f"`{DISCORD_COMMAND_DOCUMENTATION[command][1]}`: {DISCORD_COMMAND_DOCUMENTATION[command][2]}" if command is not None and command in DISCORD_COMMAND_DOCUMENTATION else MessagesTexts.HELP[LANGUAGE].replace(
		"[generalDescriptions]", "\n".join(f"- `{syntax}`: {description}" for permissionLevel, syntax, description in DISCORD_COMMAND_DOCUMENTATION.values() if permissionLevel == "general")
	).replace(
		"[trustedDescriptions]", "\n".join(f"- `{syntax}`: {description}" for permissionLevel, syntax, description in DISCORD_COMMAND_DOCUMENTATION.values() if permissionLevel == "trusted")
	).replace(
		"[ownerDescriptions]", "\n".join(f"- `{syntax}`: {description}" for permissionLevel, syntax, description in DISCORD_COMMAND_DOCUMENTATION.values() if permissionLevel == "owner")
	).replace("[emote]", DISCORD_REQUEST_ADDITION_EMOJI))

async def message_contains(source: Interaction | Message, *entries: str, obj: Group | Requests) -> None:
	"""Reacts whether the specified entry is stored in the specified object."""
	reformattedEntries = entries
	if isinstance(obj, (Group, Requests)):
		reformattedEntries = tuple(int(entry.strip("<@!> ")) for entry in entries)

	await Discord.indicateSuccess(source, "Yes." if isinstance(source, Interaction) else None) if all(entry in obj for entry in reformattedEntries) else await Discord.indicateFailure(source, "No." if isinstance(source, Interaction) else None)


async def message_getsize(source: Interaction | Message, *, obj: Cache | Group | Requests | Vectorstore) -> None:
	"""Returns the object's size."""
	await Discord.replyWithinCharacterLimit(source, f"{len(obj)}.")


async def message_load(source: Interaction | Message, filepaths: Iterable[str] | None = None, *, objects: Iterable[Cache | Group | Requests | Vectorstore], trustedGroup: Group | None = None) -> None:
	"""(Trusted command) Loads the object from the provided filepath, or the last-used filepath if none is provided."""
	for obj, filepath in (zip(objects, filepaths if filepaths is not None else repeat(None))):
		if filepath is not None and trustedGroup is not None and not obj.verify(filepath):
			trustedGroup.remove(source.user.id if isinstance(source, Interaction) else source.author.id)
			return await Discord.indicateFailure(source, MessagesTexts.DANGEROUS_FILEPATH[LANGUAGE])
		if not obj.load(filepath):
			return await Discord.indicateFailure(source, MessagesTexts.LOAD__ERROR[LANGUAGE])
	await Discord.indicateSuccess(source)


async def message_ping(interaction: Interaction | Message, *, bot: Bot) -> None:
	"""Returns the bot's latency."""
	await Discord.replyWithinCharacterLimit(interaction, MessagesTexts.PING[LANGUAGE].replace("[latency]", f"{bot.latency:.2g}"))


async def message_remove(source: Interaction | Message, *entries: str, obj: Group | Vectorstore) -> None:
	"""(Trusted command) Removes the specified entries from the specified object."""
	savedCount = 0
	if isinstance(obj, Vectorstore):
		if isinstance(source, Message) and len([word for text in entries for word in text.split()]) == len(entries):
			return await Discord.indicateFailure(source, MessagesTexts.REMOVE__SINGLE_WORDS_ONLY[LANGUAGE])
		savedCount = obj.remove(entries)
	elif isinstance(obj, Group):
		savedCount = obj.remove([int(entry.strip("<@!> ")) for entry in entries])

	if savedCount < len(entries):
		return await Discord.indicateFailure(source, MessagesTexts.REMOVE__ERROR[LANGUAGE].replace("[count]", f"{len(entries) - savedCount}").replace("[plural]", getLanguagePlural(LANGUAGE, len(entries) - savedCount)))
	await Discord.indicateSuccess(source)


async def message_save(source: Interaction | Message, filepaths: Iterable[str] | None = None, *, objects: Iterable[Cache | Group | Requests | Vectorstore], trustedGroup: Group | None = None) -> None:
	"""(Trusted command) Saves the object to the provided filepath, or the last-used filepath if none is provided."""
	for obj, filepath in (zip(objects, filepaths if filepaths is not None else repeat(None))):
		if filepath is not None and trustedGroup is not None and not obj.verify(filepath):
			trustedGroup.remove(source.user.id if isinstance(source, Interaction) else source.author.id)
			return await Discord.indicateFailure(source, MessagesTexts.DANGEROUS_FILEPATH[LANGUAGE])
		if not obj.save(filepath):
			return await Discord.indicateFailure(source, MessagesTexts.SAVE__ERROR[LANGUAGE])
	await Discord.indicateSuccess(source)


async def message_blocked(source: Interaction | Message) -> None:
	"""Returns that the user cannot run the provided command."""
	await Discord.replyWithinCharacterLimit(source, MessagesTexts.BLOCKED[LANGUAGE])

async def message_notTrusted(source: Interaction | Message, command: str) -> None:
	"""Returns that the user cannot run the provided command."""
	await Discord.replyWithinCharacterLimit(source, MessagesTexts.NOT_TRUSTED[LANGUAGE].replace("[command]", f"{command}"))

async def message_notOwner(source: Interaction | Message, command: str) -> None:
	"""Returns that the user cannot run the provided command."""
	await Discord.replyWithinCharacterLimit(source, MessagesTexts.NOT_OWNER[LANGUAGE].replace("[command]", f"{command}"))