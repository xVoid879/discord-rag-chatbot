from discord import Message
from discord.ext.commands import Bot # type: ignore
from typing import Iterable

from Settings import *
from src.components.ai import AI
from src.components.cache import Cache
from src.components.cooldown import Cooldown
from src.components.group import Group
from src.components.output import Output
from src.components.requests import Requests
from src.components.vectorstore import Vectorstore
from src.translations import MessagesTexts, getLanguagePlural
# from typing import Any, Coroutine, Iterable

# class Command:
# 	minimumArguments: int
# 	requiresTrusted: bool
# 	function: Coroutine[Any, Any, None]
# 	arguments: Iterable[Any]


async def message_add(message: Message, *entries: str, obj: Group | Vectorstore) -> None:
	"""(Trusted command) Adds the specified entry to the specified object."""
	# Temporary
	reformattedEntries = list(entries)
	if isinstance(obj, Vectorstore):
		if len([word for text in entries for word in text.split()]) == len(entries):
			await Output.replyWithinCharacterLimit(message, MessagesTexts.ADD__SINGLE_WORDS_ONLY[LANGUAGE])
			await message.add_reaction("❌")
			return
	elif isinstance(obj, Group):
		reformattedEntries = [int(e.strip("<@!> ")) for e in entries]

	if (savedCount := obj.add(reformattedEntries)) < len(entries):
		await Output.replyWithinCharacterLimit(message, MessagesTexts.ADD__ERROR[LANGUAGE].replace("count", f"{len(reformattedEntries) - savedCount}").replace("[plural]", getLanguagePlural(LANGUAGE, len(reformattedEntries) - savedCount)))
		await message.add_reaction("❌")
		return
	await message.add_reaction("✅")


async def message_ask(
	message: Message,
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
			await Output.replyWithinCharacterLimit(message, MessagesTexts.ASK__COOLDOWN[LANGUAGE].replace("[seconds]", f"{remainingCooldown:.2g}"))
			await message.add_reaction("❌")
			return
	# Check cache
	if cache is not None:
		if response := cache.getExactMatch(query):
			await Output.replyWithinCharacterLimit(message, response + "\n-# " + MessagesTexts.ASK__CACHED_RESPONSE[LANGUAGE] + (" " + MessagesTexts.ASK__AI_DISCLAIMER[LANGUAGE] if ai is not None else ""))
			return
		if response := cache.getSemanticMatch(query):
			await Output.replyWithinCharacterLimit(message, response + "\n-# " + MessagesTexts.ASK__CACHED_RESPONSE[LANGUAGE] + (" " + MessagesTexts.ASK__AI_DISCLAIMER[LANGUAGE] if ai is not None else ""))
			return
	# Retrieve context and scores from vectorstore
	context = "\n\n-------------".join(f"__(Estimated relevance: **{score:.2%}**)__\n{text}".strip() for text, score in vectorstore.query(query)) if vectorstore is not None else MessagesTexts.ASK__DEFAULT_CONTEXT[LANGUAGE]
	if context and context != MessagesTexts.ASK__DEFAULT_CONTEXT[LANGUAGE]:
		context = "\n-------------" + context
	# If context is required, and no context is found, return error
	elif AI_REQUIRE_CONTEXT:
		await Output.replyWithinCharacterLimit(message, MessagesTexts.ASK__ERROR_IF_NO_CONTEXT[LANGUAGE])
		return

	# Retrieve AI response
	response = ai.query(query, context) if ai is not None else MessagesTexts.ASK__RETURN_VECTORSTORE[LANGUAGE].replace("[messages]", context)
	# Send message to user, and cache for future
	await Output.replyWithinCharacterLimit(message, response + ("\n-# " + MessagesTexts.ASK__AI_DISCLAIMER[LANGUAGE] if ai is not None else ""))
	if cache is not None:
		cache[query] = (response, cache.embed(query))


async def message_clear(message: Message, *, objects: Iterable[Cache | Group | Requests | Vectorstore]) -> None:
	"""(Trusted command) Clears the specified object."""
	for obj in objects: obj.clear()
	await message.add_reaction("✅")


async def message_help(message: Message) -> None:
	"""Prints the help message."""
	await Output.replyWithinCharacterLimit(message, MessagesTexts.HELP[LANGUAGE].replace("[descriptions]", "\n".join(f"- {description}" for description in DISCORD_COMMAND_DOCUMENTATION.values())).replace("[emote]", DISCORD_REQUEST_ADDITION_EMOJI))

# TODO: Extend to allow checking if a recipient ID has any requests pending.
async def message_isin(message: Message, entry: str, *, obj: Group) -> None:
	"""Reacts whether the specified entry is stored in the specified object."""
	reformattedEntry = entry
	if isinstance(obj, Group):
		reformattedEntry = int(entry.strip("<@!> "))

	for emote in (MessagesTexts.IS_IN__FOUND_EMOTES[LANGUAGE] if reformattedEntry in obj else MessagesTexts.IS_IN__NOT_FOUND_EMOTES[LANGUAGE]):
		await message.add_reaction(emote)


# TODO: Allow `filepath` to be an iterable as well?
async def message_load(message: Message, filepath: str | None = None, *, objects: Iterable[Cache | Group | Requests | Vectorstore], trustedGroup: Group | None = None) -> None:
	"""(Trusted command) Loads the object from the provided filepath, or the last-used filepath if none is provided."""
	for obj in objects:
		if filepath is not None and trustedGroup is not None and not obj.verify(filepath):
			await Output.replyWithinCharacterLimit(message, "An invalid filepath was specified that could potentially have caused damage if executed. As a precautionary measure, you have been distrusted.\n-# Contact another trusted user if this is a misunderstanding.")
			trustedGroup.remove(message.author.id)
			await message.add_reaction("❌")
			return
		if not obj.load(filepath):
			await Output.replyWithinCharacterLimit(message, MessagesTexts.LOAD__ERROR[LANGUAGE])
			await message.add_reaction("❌")
			return
	await message.add_reaction("✅")


async def message_ping(message: Message, *, bot: Bot) -> None:
	"""Returns the bot's latency."""
	await Output.replyWithinCharacterLimit(message, MessagesTexts.PING[LANGUAGE].replace("[latency]", f"{bot.latency:.2g}"))


async def message_remove(message: Message, *entries: str, obj: Group | Vectorstore) -> None:
	"""(Trusted command) Removes the specified entries from the specified object."""
	reformattedEntries = list(entries)
	if isinstance(obj, Vectorstore):
		if len([word for text in entries for word in text.split()]) == len(entries):
			await Output.replyWithinCharacterLimit(message, MessagesTexts.REMOVE__SINGLE_WORDS_ONLY[LANGUAGE])
			await message.add_reaction("❌")
			return
	elif isinstance(obj, Group):
		reformattedEntries = [int(e.strip("<@!> ")) for e in entries]

	if (savedCount := obj.remove(reformattedEntries)) < len(entries):
		await Output.replyWithinCharacterLimit(message, MessagesTexts.REMOVE__ERROR[LANGUAGE].replace("count", f"{len(reformattedEntries) - savedCount}").replace("[plural]", getLanguagePlural(LANGUAGE, len(reformattedEntries) - savedCount)))
		await message.add_reaction("❌")
		return
	await message.add_reaction("✅")


# TODO: Allow `filepath` to be an iterable as well?
async def message_save(message: Message, filepath: str | None = None, *, objects: Iterable[Cache | Group | Requests | Vectorstore], trustedGroup: Group | None = None) -> None:
	"""(Trusted command) Saves the object to the provided filepath, or the last-used filepath if none is provided."""
	for obj in objects:
		if filepath is not None and trustedGroup is not None and not obj.verify(filepath):
			await Output.replyWithinCharacterLimit(message, "An invalid filepath was specified that could potentially have caused damage if executed. As a precautionary measure, you have been distrusted.\n-# Contact another trusted user if this is a misunderstanding.")
			trustedGroup.remove(message.author.id)
			await message.add_reaction("❌")
			return
		if not obj.save(filepath):
			await Output.replyWithinCharacterLimit(message, MessagesTexts.SAVE__ERROR[LANGUAGE])
			await message.add_reaction("❌")
			return
	await message.add_reaction("✅")


async def message_notTrusted(message: Message, command: str) -> None:
	"""Returns that the user cannot run the provided command."""
	await Output.replyWithinCharacterLimit(message, MessagesTexts.NOT_TRUSTED[LANGUAGE].replace("[command]", f"{command}"))