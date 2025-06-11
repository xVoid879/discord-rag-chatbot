from discord import Intents, Member, Message, Reaction
from discord.ext.commands import Bot # type: ignore
from pydantic import SecretStr
from sys import argv
import os

from Settings import *
from src.messages import *
from src.reactions import *
from src.translations import MainTexts, RequestsTexts

if len(argv) < 1: raise RuntimeError(MainTexts.NO_ARGUMENTS_FOUND[LANGUAGE])
CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(argv[0]))
if len(argv) < 2: raise RuntimeError(MainTexts.NO_DISCORD_BOT_TOKEN[LANGUAGE])
DISCORD_BOT_TOKEN = SecretStr(argv[1])
AI_API_KEY = SecretStr(argv[2]) if len(argv) >= 3 else None

intents = Intents.default()
intents.message_content = True
bot = Bot(command_prefix="", intents=intents)


ai = AI(AI_API_KEY, AI_SYSTEM_PROMPT, AI_TEMPERATURE, AI_MAX_INPUT_CHARACTERS) if AI_API_KEY and AI_SYSTEM_PROMPT else None
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
	if message.author.id in blockedGroup and (bot.owner_ids is None or message.author.id not in bot.owner_ids):
		await message.add_reaction("❌")
		return
	# Remove ping from message
	originalInput = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
	# If message is for another bot, ignore
	if any(originalInput.startswith(otherBotPrefix) for otherBotPrefix in DISCORD_OTHER_BOT_PREFIXES):
		return
	commandSubcommandString = originalInput.split(maxsplit=3)
	# If bot was pinged without any other commands: print help message
	if not commandSubcommandString:
		await message_help(message)
		return
	# Otherwise decipher command:
	# TODO: Convert most of these into slash commands
	# TODO: Consolidate block/trust and unblock/distrust under addrole/removerole
	# TODO: Rename permitting/revoking to waiving/reinstating?
	argumentsCount = len(commandSubcommandString)
	match command := commandSubcommandString[0].casefold():
		case "addtext":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_add(message, " ".join(commandSubcommandString[1:]), obj=vectorstore)
		case "block":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_add(message, *commandSubcommandString[1:], obj=blockedGroup)
		case "clear":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else:
				match commandSubcommandString[1].casefold():
					case "all":
						# await message_clear(message, objects=(blockedGroup, cache, permittingGroup, permissionRequests, trustedGroup, vectorstore, vectorstoreRequests))
						await message_clear(message, objects=(blockedGroup, cache, permittingGroup, permissionRequests, trustedGroup, vectorstoreRequests))
					case "blocked_group":
						await message_clear(message, objects=(blockedGroup,))
					case "cache":
						await message_clear(message, objects=(cache,))
					case "permitting_group":
						await message_clear(message, objects=(permittingGroup,))
					case "permitting_requests":
						await message_clear(message, objects=(permissionRequests,))
					case "trusted_group":
						await message_clear(message, objects=(trustedGroup,))
					# case "vectorstore":
					# 	await message_clear(message, objects=(vectorstore,))
					case "vectorstore_requests":
						await message_clear(message, objects=(vectorstoreRequests,))
					case _:
						await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
		case "distrust":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_remove(message, *commandSubcommandString[1:], obj=trustedGroup)
		case "hasrole":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			else:
				match commandSubcommandString[1].casefold():
					case "blocked":
						await message_isin(message, commandSubcommandString[2] if argumentsCount >= 3 else str(message.author.id), obj=blockedGroup)
					case "permitting":
						await message_isin(message, commandSubcommandString[2] if argumentsCount >= 3 else str(message.author.id), obj=permittingGroup)
					case "trusted":
						await message_isin(message, commandSubcommandString[2] if argumentsCount >= 3 else str(message.author.id), obj=trustedGroup)
					case _:
						await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
		case "help":
			await message_help(message)
		case "load":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else:
				match commandSubcommandString[1].casefold():
					case "all":
						await message_load(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(blockedGroup, cache, permittingGroup, permissionRequests, trustedGroup, vectorstore, vectorstoreRequests), trustedGroup=trustedGroup)
					case "blocked_group":
						await message_load(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(blockedGroup,), trustedGroup=trustedGroup)
					case "cache":
						await message_load(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(cache,), trustedGroup=trustedGroup)
					case "permitting_group":
						await message_load(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(permittingGroup,), trustedGroup=trustedGroup)
					case "permitting_requests":
						await message_load(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(permissionRequests,), trustedGroup=trustedGroup)
					case "trusted_group":
						await message_load(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(trustedGroup,), trustedGroup=trustedGroup)
					case "vectorstore":
						await message_load(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(vectorstore,), trustedGroup=trustedGroup)
					case "vectorstore_requests":
						await message_load(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(vectorstoreRequests,), trustedGroup=trustedGroup)
					case _:
						await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
		case "permit":
			await reaction_newOrUpdateRequest(message, message.author, requests=permissionRequests)
		case "ping":
			await message_ping(message, bot=bot)
		# case "removetext":
		# 	if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
		# 	elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
		# 	else: await message_remove(message, " ".join(commandSubcommandString[1:]), obj=vectorstore)
		case "revoke":
			await message_remove(message, str(message.author.id), obj=permittingGroup)
		case "save":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else:
				match commandSubcommandString[1].casefold():
					case "all":
						await message_save(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(blockedGroup, cache, permittingGroup, permissionRequests, trustedGroup, vectorstore, vectorstoreRequests), trustedGroup=trustedGroup)
					case "blocked_group":
						await message_save(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(blockedGroup,), trustedGroup=trustedGroup)
					case "cache":
						await message_save(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(cache,), trustedGroup=trustedGroup)
					case "permitting_group":
						await message_save(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(permittingGroup,), trustedGroup=trustedGroup)
					case "permitting_requests":
						await message_save(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(permissionRequests,), trustedGroup=trustedGroup)
					case "trusted_group":
						await message_save(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(trustedGroup,), trustedGroup=trustedGroup)
					case "vectorstore":
						await message_save(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(vectorstore,), trustedGroup=trustedGroup)
					case "vectorstore_requests":
						await message_save(message, " ".join(commandSubcommandString[2:]) if argumentsCount >= 3 else None, objects=(vectorstoreRequests,), trustedGroup=trustedGroup)
					case _:
						await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
		case "trust":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_add(message, *commandSubcommandString[1:], obj=trustedGroup)
		case "unblock":
			if argumentsCount < 2: await Output.replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command])
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_remove(message, *commandSubcommandString[1:], obj=blockedGroup)
		case _:
			await message_ask(message, originalInput, ai=ai, cache=cache, cooldown=cooldown, vectorstore=vectorstore)


@bot.event
async def on_reaction_add(reaction: Reaction, member: Member) -> None:
	"""Decodes desired action upon a new reaction being added."""
	# If the reaction is not on a request message...
	if all((reaction.message not in vectorstoreRequests, reaction.message not in permissionRequests)):
		# ...and it's not the designated emoji, or by a non-trusted user, ignore
		# TODO: Also ignore if recipient is not in the server
		if reaction.emoji != DISCORD_REQUEST_ADDITION_EMOJI or member.id not in trustedGroup:
			return
		if reaction.message.author.id == member.id or reaction.message.author.id in permittingGroup:
			await reaction_requestAnswered(reaction, True, requests=vectorstoreRequests, obj=vectorstore)
			return
		await reaction_newOrUpdateRequest(reaction, member, requests=vectorstoreRequests)
	# If it is on a request message...
	else:
		# ...and it's not one of the two accepted emojis, or not by the recipient, ignore
		if reaction.emoji not in {"✅", "❌"}: return
		# Otherwise check both the vectorstore requests list and the permission requests list
		for requestsList, obj in ((vectorstoreRequests, vectorstore), (permissionRequests, permittingGroup)):
			if (record := requestsList[reaction.message]) is None or member.id != record["recipientID"]: continue
			await reaction_requestAnswered(reaction, reaction.emoji == "✅", requests=requestsList, obj=obj)


bot.run(DISCORD_BOT_TOKEN.get_secret_value())