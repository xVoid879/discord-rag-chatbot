from discord import Message
from discord.ext.commands import Bot

from Settings import *
from src.components.ai import AI
from src.components.cache import Cache
from src.components.cooldown import Cooldown
from src.components.group import Group
from src.components.vectorstore import Vectorstore
# from typing import Any, Coroutine, Iterable

# class Command:
# 	minimumArguments: int
# 	requiresTrusted: bool
# 	function: Coroutine[Any, Any, None]
# 	arguments: Iterable[Any]


async def message_add(message: Message, *entries: str, obj: Group | Vectorstore) -> None:
	"""(Privileged command) Adds the specified entry to the specified object."""
	# Temporary
	reformattedEntries = list(entries)
	if isinstance(obj, Vectorstore):
		if len([word for text in entries for word in text.split()]) == len(entries):
			await message.reply(f"All texts received solely consisted of individual words. Make sure to wrap your texts in quotation marks.", mention_author=False)
			await message.add_reaction("❌")
			return
	elif isinstance(obj, Group):
		reformattedEntries = [int(e.strip("<@!> ")) for e in entries]

	if (savedCount := obj.add(reformattedEntries)) < len(entries):
		await message.reply(f"{len(reformattedEntries) - savedCount} text{'' if len(reformattedEntries) - savedCount == 1 else 's'} failed to be added.", mention_author=False)
		await message.add_reaction("❌")
		return
	await message.add_reaction("✅")


async def message_ask(
	message: Message,
	query: str,
	*,
	ai: AI,
	cache: Cache | None = None,
	cooldown: Cooldown | None = None,
	vectorstore: Vectorstore | None = None
) -> None:
	"""Generate an answer to the provided query, subject to a cooldown."""
	# Check cooldown
	if cooldown is not None:
		if (remainingCooldown := cooldown.getRemainingTime()) > 0.:
			await message.reply(COOLDOWN_MESSAGE + f" ({remainingCooldown:.2g} seconds remaining)", mention_author=False)
			await message.add_reaction("❌")
			return
	# Check cache
	if cache is not None:
		if response := cache.getExactMatch(query):
			await message.reply(response + f"\n-# Cached response. {AI_DISCLAIMER}", mention_author=False)
			# await message.add_reaction("✅")
			return
		if response := cache.getSemanticMatch(query):
			await message.reply(response + f"\n-# Cached response. {AI_DISCLAIMER}", mention_author=False)
			# await message.add_reaction("✅")
			return
	# Retrieve context from vectorstore
	context = "\n- ".join(text for text, _ in vectorstore.query(query)) if vectorstore is not None else None
	# If context is required, and no context is found, return error
	if context:
		context = "- " + context
	elif AI_ERROR_IF_NO_CONTEXT:
		await message.reply(AI_ERROR_IF_NO_CONTEXT, mention_author=False)
		# await message.add_reaction("✅")
		return

	# Retrieve AI response
	response = ai.query(query, context) if AI_ENABLE else "Here are the relevant messages in my corpus relating to your question:\n" + ("- None" if context is None else context)
	# Send message to user, and cache for future
	await message.reply(response + f"\n-# {AI_DISCLAIMER}", mention_author=False)
	# await message.add_reaction("✅")
	if cache is not None:
		cache[query] = (response, cache.embed(query))


async def message_isin(message: Message, entry: str, *, obj: Group) -> None:
	"""Peacts whether the specified entry is stored in the specified object."""
	reformattedEntry = entry
	if isinstance(obj, Group):
		reformattedEntry = int(entry.strip("<@!> "))

	if reformattedEntry in obj:
		await message.add_reaction("🇾")
		await message.add_reaction("🇪")
		await message.add_reaction("🇸")
	else:
		await message.add_reaction("🇳")
		await message.add_reaction("🇴")


async def message_load(message: Message, filepath: str | None = None, *, obj: Group | Vectorstore) -> None:
	"""(Privileged command) Loads the object from the provided filepath, or the last-used filepath if none is provided."""
	if not obj.load(filepath):
		await message.reply(f"An error occurred while loading the object.", mention_author=False)
		await message.add_reaction("❌")
		return
	await message.add_reaction("✅")


async def message_ping(message: Message, *, bot: Bot) -> None:
	"""(Privileged command) Saves the vectorstore to the provided filepath, or the last-used filepath if none is provided."""
	await message.reply(f"My latency is {bot.latency:.2g} seconds.", mention_author=False)


async def message_remove(message: Message, *entries: str, obj: Group | Vectorstore) -> None:
	"""(Privileged command) Blocks the specified user from using the bot."""
	reformattedEntries = list(entries)
	if isinstance(obj, Vectorstore):
		if len([word for text in entries for word in text.split()]) == len(entries):
			await message.reply(f"All texts received solely consisted of individual words. Make sure to wrap your texts in quotation marks.", mention_author=False)
			await message.add_reaction("❌")
			return
	elif isinstance(obj, Group):
		reformattedEntries = [int(e.strip("<@!> ")) for e in entries]

	if (savedCount := obj.remove(reformattedEntries)) < len(entries):
		await message.reply(f"{len(reformattedEntries) - savedCount} text{'' if len(reformattedEntries) - savedCount == 1 else 's'} failed to be removed.", mention_author=False)
		await message.add_reaction("❌")
		return
	await message.add_reaction("✅")


async def message_save(message: Message, filepath: str | None = None, *, obj: Group | Vectorstore | None = None) -> None:
	"""(Privileged command) Saves the object to the provided filepath, or the last-used filepath if none is provided."""
	if obj is None:
		await message.reply(f"Error: No object exists to save.", mention_author=False)
		await message.add_reaction("❌")
		return
	if not obj.save(filepath):
		await message.reply(f"An error occurred while saving the object.", mention_author=False)
		await message.add_reaction("❌")
		return
	await message.add_reaction("✅")


async def message_notTrusted(message: Message, command: str) -> None:
	"""(Privileged command) Returns an error message."""
	await message.reply(f"Sorry, `{command}` is a trusted-only command.", mention_author=False)