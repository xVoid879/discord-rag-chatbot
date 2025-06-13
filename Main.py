from discord import Intents, Interaction, Member, Message, Reaction
from discord.app_commands import describe
from discord.ext.commands import Bot # type: ignore
from os.path import abspath, dirname
from pydantic import SecretStr
from sys import argv
from typing import Literal

from Settings import *
from src.messages import *
from src.reactions import *
from src.translations import MainTexts, RequestsTexts

if len(argv) < 1: raise RuntimeError(MainTexts.NO_ARGUMENTS_FOUND[LANGUAGE])
CURRENT_DIRECTORY = abspath(dirname(argv[0]))
if len(argv) < 2: raise RuntimeError(MainTexts.NO_DISCORD_BOT_TOKEN[LANGUAGE])
DISCORD_BOT_TOKEN = SecretStr(argv[1])
AI_API_KEY = SecretStr(argv[2]) if len(argv) >= 3 else None

intents = Intents.default()
intents.message_content = True

class _Bot(Bot):
	async def setup_hook(self):
		await self.tree.sync()

bot = _Bot(command_prefix="/", intents=intents)


ai = AI(AI_API_KEY, AI_SYSTEM_PROMPT, AI_TEMPERATURE, AI_MAX_INPUT_CHARACTERS, AI_MAX_OUTPUT_CHARACTERS) if AI_API_KEY and AI_SYSTEM_PROMPT else None
cooldown = Cooldown(COOLDOWN_DURATION, COOLDOWN_CHECK_INTERVAL, COOLDOWN_MAX_QUERIES_BEFORE_ACTIVATION)
cache = Cache(CACHE_MAX_SIZE, CACHE_EXPIRATION_TIME, CACHE_SEMANTIC_SIMILARITY_THRESHOLD, CACHE_FILEPATH)
permissionRequests = Requests(RequestsTexts.PERMISSION_REQUEST[LANGUAGE], REQUESTS_PERMITTING_FILEPATH)
vectorstoreRequests = Requests(RequestsTexts.VECTORSTORE_REQUEST[LANGUAGE], REQUESTS_VECTORSTORE_FILEPATH)
vectorstore = Vectorstore(VECTORSTORE_FILEPATH, VECTORSTORE_CONTEXT_RELEVANCE_THRESHOLD, VECTORSTORE_SEGMENT_SIZE)
trustedGroup = Group(GROUPS_TRUSTED_IDS_FILEPATH)
blockedGroup = Group(GROUPS_BLOCKED_IDS_FILEPATH)
permittingGroup = Group(GROUPS_PERMITTING_IDS_FILEPATH)

@bot.event
async def on_message(message: Message) -> None:
	"""Decode desired action upon being pinged."""
	# Thank you to Opal for contributing code to this.

	# If bot was not mentioned or mentioned itself, ignore
	if bot.user not in message.mentions or message.author == bot.user or bot.user is None:
		return
	# If user is blacklisted and not an owner, ignore
	if message.author.id in blockedGroup and not await bot.is_owner(message.author):
		return await message_blocked(message)
	# Remove ping from message
	originalInput = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
	# If message is for another bot, ignore
	if any(originalInput.startswith(otherBotPrefix) for otherBotPrefix in DISCORD_OTHER_BOT_PREFIXES):
		return
	commandSubcommandString = originalInput.split(maxsplit=2)
	# If bot was pinged without any other commands: print help message
	if not commandSubcommandString:
		return await message_help(message)
	# Otherwise decipher command:
	# TODO: Convert /permit into a slash command
	# TODO: Rename permitting/revoking to waiving/reinstating?
	argumentsCount = len(commandSubcommandString)
	match commandSubcommandString[0].casefold():
		case "help":
			return await message_help(message, commandSubcommandString[1] if argumentsCount >= 2 else None)
		case "permit":
			return await reaction_newOrUpdateRequest(message, message.author, requests=permissionRequests)
		case _:
			return await message_ask(message, originalInput, ai=ai, cache=cache, cooldown=cooldown, vectorstore=vectorstore)


@bot.event
async def on_reaction_add(reaction: Reaction, member: Member) -> None:
	"""Decodes desired action upon a new reaction being added."""
	if bot.user is None or member == bot.user:
		return
	# If the reaction is not on a request message...
	if all((reaction.message not in vectorstoreRequests, reaction.message not in permissionRequests)):
		# ...and it's not the designated emoji, or by a non-trusted user, ignore
		# TODO: Also ignore if recipient is not in the server
		if reaction.emoji != DISCORD_REQUEST_ADDITION_EMOJI or member.id not in trustedGroup:
			return
		if reaction.message.author.id == member.id or reaction.message.author.id in permittingGroup:
			return await reaction_requestAnswered(reaction, True, requests=vectorstoreRequests, obj=vectorstore, bot=bot)
		await reaction_newOrUpdateRequest(reaction, member, requests=vectorstoreRequests)
	# If it is on a request message...
	else:
		# ...and it's not one of the two accepted emojis, or not by the recipient, ignore
		if reaction.emoji not in {"✅", "❌"}: return
		# Otherwise check both the vectorstore requests list and the permission requests list
		for requestsList, obj in ((vectorstoreRequests, vectorstore), (permissionRequests, permittingGroup)):
			if (record := requestsList[reaction.message]) is None or member.id != record["recipientID"]: continue
			await reaction_requestAnswered(reaction, reaction.emoji == "✅", requests=requestsList, obj=obj, bot=bot)

# TODO: Deleting a request message cancels the corresponding request


@bot.tree.command(name="add", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["add"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	object = "The object being added to.",
	entry = "The entry being added to the object."
)
async def command_add(interaction: Interaction, object: Literal["Blocked Group", "Trusted Group", "Vectorstore"], entry: str) -> None:
	if interaction.user.id in blockedGroup and not await bot.is_owner(interaction.user): return await message_blocked(interaction)
	if interaction.user.id not in trustedGroup and not await bot.is_owner(interaction.user): return await message_notTrusted(interaction, "/add")
	if object == "Vectorstore":
		if (message := await Output.getMessageFromURL(entry, bot=bot)) is None: return await Output.indicateFailure(interaction)
		if message.author == interaction.user or message.author.id in permittingGroup:
			await reaction_requestAnswered(message, True, requests=vectorstoreRequests, obj=vectorstore, bot=bot)
			return await Output.indicateSuccess(interaction)
		return await reaction_newOrUpdateRequest(message, interaction.user, requests=vectorstoreRequests)
	else: await message_add(interaction, entry, obj=blockedGroup if object == "Blocked Group" else trustedGroup)


@bot.tree.command(name="ask", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["ask"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	query = "Your query.",
)
async def command_ask(interaction: Interaction, query: str) -> None:
	if interaction.user.id in blockedGroup and not await bot.is_owner(interaction.user): return await message_blocked(interaction)
	await message_ask(interaction, query, ai=ai, cache=cache, cooldown=cooldown, vectorstore=vectorstore)


@bot.tree.command(name="clear", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["clear"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	object = "The object to clear."
)
async def command_clear(interaction: Interaction, object: Literal["All", "Blocked Group", "Cache", "Permitting Group", "Permitting Requests", "Trusted Group", "Vectorstore", "Vectorstore Requests"]) -> None:
	if interaction.user.id in blockedGroup and not await bot.is_owner(interaction.user): return await message_blocked(interaction)
	if interaction.user.id not in trustedGroup and not await bot.is_owner(interaction.user): return await message_notTrusted(interaction, "/clear")
	await message_clear(interaction, objects=(
		(blockedGroup,) if object == "Blocked Group"
		else (cache,) if object == "Cache"
		else (permittingGroup,) if object == "Permitting Group"
		else (permissionRequests,) if object == "Permitting Requests"
		else (trustedGroup,) if object == "Trusted Group"
		else (vectorstore,) if object == "Vectorstore"
		else (vectorstoreRequests,) if object == "Vectorstore Requests"
		else (blockedGroup, cache, permittingGroup, permissionRequests, trustedGroup, vectorstore, vectorstoreRequests)
	))


@bot.tree.command(name="contains", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["contains"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	group = "The group to test.",
	user = "(Optional) The user ID to test. If omitted, defaults to yourself."
)
async def command_contains(interaction: Interaction, group: Literal["Blocked Group", "Permitting Group", "Permitting Requests", "Trusted Group", "Vectorstore Requests"], user: str | None = None) -> None:
	if interaction.user.id in blockedGroup and not await bot.is_owner(interaction.user): return await message_blocked(interaction)
	await message_contains(interaction, user if user is not None else str(interaction.user.id), obj=(
		blockedGroup if group == "Blocked Group"
		else permittingGroup if group == "Permitting Group"
		else permissionRequests if group == "Permitting Requests"
		else trustedGroup if group == "Trusted Group"
		else vectorstoreRequests
	))

@bot.tree.command(name="getsize", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["getsize"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	object = "The object whose size to return.",
)
async def command_getsize(interaction: Interaction, object: Literal["Blocked Group", "Cache", "Permitting Group", "Permitting Requests", "Trusted Group", "Vectorstore", "Vectorstore Requests"]) -> None:
	if interaction.user.id in blockedGroup and not await bot.is_owner(interaction.user): return await message_blocked(interaction)
	await message_getsize(interaction, obj=(
		blockedGroup if object == "Blocked Group"
		else cache if object == "Cache"
		else permittingGroup if object == "Permitting Group"
		else permissionRequests if object == "Permitting Requests"
		else trustedGroup if object == "Trusted Group"
		else vectorstore if object == "Vectorstore"
		else vectorstoreRequests
	))


@bot.tree.command(name="help", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["help"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	command = "(Optional) The command you want info about. If omitted, prints info about all commands."
)
async def command_help(interaction: Interaction, command: str | None = None) -> None:
	if interaction.user.id in blockedGroup and not await bot.is_owner(interaction.user): return await message_blocked(interaction)
	await message_help(interaction, command)


@bot.tree.command(name="load", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["load"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	object = "The object to load.",
	filepath = "(Optional) The filepath to use. If omitted, the most recent filepath is used."
)
async def command_load(interaction: Interaction, object: Literal["All", "Blocked Group", "Cache", "Permitting Group", "Permitting Requests", "Trusted Group", "Vectorstore", "Vectorstore Requests"], filepath: str | None = None) -> None:
	if not await bot.is_owner(interaction.user): return await message_notOwner(interaction, "/load")
	await message_load(interaction, filepath if object != "All" else None, objects=(
		(blockedGroup,) if object == "Blocked Group"
		else (cache,) if object == "Cache"
		else (permittingGroup,) if object == "Permitting Group"
		else (permissionRequests,) if object == "Permitting Requests"
		else (trustedGroup,) if object == "Trusted Group"
		else (vectorstore,) if object == "Vectorstore"
		else (vectorstoreRequests,) if object == "Vectorstore Requests"
		else (blockedGroup, cache, permittingGroup, permissionRequests, trustedGroup, vectorstore, vectorstoreRequests)
	))


# @bot.tree.command(name="permit", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["permit"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
# async def command_permit(interaction: Interaction) -> None:
# 	# Intentionally allow blocked users to use this command
# 	await reaction_newOrUpdateRequest(interaction, interaction.user, requests=permissionRequests)


@bot.tree.command(name="ping", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["ping"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
async def command_ping(interaction: Interaction) -> None:
	"""Returns the bot's latency."""
	if interaction.user.id in blockedGroup and not await bot.is_owner(interaction.user): return await message_blocked(interaction)
	await message_ping(interaction, bot=bot)


@bot.tree.command(name="remove", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["remove"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	object = "The object being removed from.",
	entry = "The entry being removed from the object."
)
# async def command_remove(interaction: Interaction, object: Literal["Blocked Group", "Trusted Group", "Vectorstore"], entry: str) -> None:
async def command_remove(interaction: Interaction, object: Literal["Blocked Group", "Trusted Group"], entry: str) -> None:
	if interaction.user.id in blockedGroup and not await bot.is_owner(interaction.user): return await message_blocked(interaction)
	if interaction.user.id not in trustedGroup and not await bot.is_owner(interaction.user): return await message_notTrusted(interaction, "/remove")
	await message_remove(interaction, entry, obj=blockedGroup if object == "Blocked Group" else trustedGroup)
	# await message_remove(interaction, entry, obj=blockedGroup if object == "Blocked Group" else trustedGroup if object == "Trusted Group" else vectorstore)


@bot.tree.command(name="revoke", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["revoke"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
async def command_revoke(interaction: Interaction) -> None:
	# Intentionally allow blocked users to use this command
	await message_remove(interaction, str(interaction.user.id), obj=permittingGroup)


@bot.tree.command(name="save", description=Output.truncate(DISCORD_COMMAND_DOCUMENTATION["save"][1], Output.DISCORD_DESCRIPTION_CHARACTER_LIMIT))
@describe(
	object = "The object to save.",
	filepath = "(Optional) The filepath to use. If omitted, the most recent filepath is used."
)
async def command_save(interaction: Interaction, object: Literal["All", "Blocked Group", "Cache", "Permitting Group", "Permitting Requests", "Trusted Group", "Vectorstore", "Vectorstore Requests"], filepath: str | None = None) -> None:
	if not await bot.is_owner(interaction.user): return await message_notOwner(interaction, "/save")
	await message_save(interaction, filepath if object != "All" else None, objects=(
		(blockedGroup,) if object == "Blocked Group"
		else (cache,) if object == "Cache"
		else (permittingGroup,) if object == "Permitting Group"
		else (permissionRequests,) if object == "Permitting Requests"
		else (trustedGroup,) if object == "Trusted Group"
		else (vectorstore,) if object == "Vectorstore"
		else (vectorstoreRequests,) if object == "Vectorstore Requests"
		else (blockedGroup, cache, permittingGroup, permissionRequests, trustedGroup, vectorstore, vectorstoreRequests)
	))



bot.run(DISCORD_BOT_TOKEN.get_secret_value())