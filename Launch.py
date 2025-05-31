from discord import Intents, Member, Message, Reaction
from discord.ext.commands import Bot
from pydantic import SecretStr
from sys import argv
import os

from Settings import *
from src.messages import *
from src.reactions import *

if len(argv) < 1: raise RuntimeError("No arguments found when launching the chatbot.")
CURRENT_DIRECTORY = os.path.dirname(argv[0])
if len(argv) < 2: raise RuntimeError("No Discord bot token provided (must be 1st argument).")
DISCORD_BOT_TOKEN = SecretStr(argv[1])
if len(argv) < 3: raise RuntimeError("No Groq API key provided (must be 2nd argument).")
AI_API_KEY = SecretStr(argv[2])

intents = Intents.default()
intents.message_content = True
bot = Bot(command_prefix="", intents=intents)


ai = AI(AI_API_KEY, AI_SYSTEM_PROMPT, AI_TEMPERATURE, AI_MAX_INPUT_CHARACTERS)
cooldown = Cooldown(COOLDOWN_DURATION, COOLDOWN_CHECK_INTERVAL, COOLDOWN_MAX_QUERIES_BEFORE_ACTIVATION) if COOLDOWN_DURATION is not None and COOLDOWN_DURATION > 0. else None
cache = Cache(CACHE_MAX_SIZE, CACHE_EXPIRATION_TIME, CACHE_SEMANTIC_SIMILARITY_THRESHOLD) if CACHE_MAX_SIZE > 0 else None
requests = Requests(REQUESTS_ADDITION_MESSAGE, REQUESTS_ADDITION_KEYWORDS)
vectorstore = Vectorstore(VECTORSTORE_FILEPATH, VECTORSTORE_CONTEXT_RELEVANCE_THRESHOLD, VECTORSTORE_SEGMENT_SIZE)
trustedGroup = Group(DISCORD_TRUSTED_IDS_FILEPATH)
blockedGroup = Group(DISCORD_BLOCKED_IDS_FILEPATH)

@bot.event
async def on_message(message: Message) -> None:
	"""Decode desired action upon being pinged."""
	# Thank you to Opal for contributing code to this.
	global vectorstore
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
	# If bot was pinged without any other commands:
	if not commandSubcommandString:
		await replyWithinCharacterLimit(message, DISCORD_HELP_MESSAGE, 2000)
		return
	# Otherwise decipher command:
	argumentsCount = len(commandSubcommandString)
	match command := commandSubcommandString[0].casefold():
		case "addtext":
			if argumentsCount < 2: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_add(message, " ".join(commandSubcommandString[1:]), obj=vectorstore)
		case "block":
			if argumentsCount < 2: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_add(message, *commandSubcommandString[1:], obj=blockedGroup)
		case "distrust":
			if argumentsCount < 2: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_remove(message, *commandSubcommandString[1:], obj=trustedGroup)
		case "hasrole":
			if argumentsCount < 3: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
			else:
				match commandSubcommandString[1].casefold():
					case "blocked":
						await message_isin(message, commandSubcommandString[1], obj=blockedGroup)
					case "trusted":
						await message_isin(message, commandSubcommandString[1], obj=trustedGroup)
					case _:
						await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
		case "load":
			if argumentsCount < 2: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else:
				match commandSubcommandString[1].casefold():
					case "blocked":
						await message_load(message, os.path.join(CURRENT_DIRECTORY, " ".join(commandSubcommandString[2:])) if argumentsCount >= 3 else None, obj=blockedGroup)
					case "trusted":
						await message_load(message, os.path.join(CURRENT_DIRECTORY, " ".join(commandSubcommandString[2:])) if argumentsCount >= 3 else None, obj=trustedGroup)
					case "vectorstore":
						await message_load(message, os.path.join(CURRENT_DIRECTORY, " ".join(commandSubcommandString[2:])) if argumentsCount >= 3 else None, obj=vectorstore)
					case _:
						await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
		case "ping":
			await message_ping(message, bot=bot)
		# case "removetext":
		# 	if argumentsCount < 2: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
		# 	elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
		# 	else: await message_remove(message, " ".join(commandSubcommandString[1:]), obj=vectorstore)
		case "save":
			if argumentsCount < 2: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else:
				match commandSubcommandString[1].casefold():
					case "blocked":
						await message_save(message, os.path.join(CURRENT_DIRECTORY, " ".join(commandSubcommandString[2:])) if argumentsCount >= 3 else None, obj=blockedGroup)
					case "trusted":
						await message_save(message, os.path.join(CURRENT_DIRECTORY, " ".join(commandSubcommandString[2:])) if argumentsCount >= 3 else None, obj=trustedGroup)
					case "vectorstore":
						await message_save(message, os.path.join(CURRENT_DIRECTORY, " ".join(commandSubcommandString[2:])) if argumentsCount >= 3 else None, obj=vectorstore)
					case _:
						await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
		case "trust":
			if argumentsCount < 2: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_add(message, *commandSubcommandString[1:], obj=trustedGroup)
		case "unblock":
			if argumentsCount < 2: await replyWithinCharacterLimit(message, DISCORD_COMMAND_DOCUMENTATION[command], 2000)
			elif message.author.id not in trustedGroup: await message_notTrusted(message, command)
			else: await message_remove(message, *commandSubcommandString[1:], obj=blockedGroup)
		case _:
			await message_ask(message, originalInput, ai=ai, cache=cache, cooldown=cooldown, vectorstore=vectorstore)


@bot.event
async def on_reaction_add(reaction: Reaction, member: Member) -> None:
	# If the reaction is not on a request message...
	if reaction.message not in requests:
		# ...and it's not the designated emoji, or by a non-trusted user, ignore
		if reaction.emoji != DISCORD_REQUEST_ADDITION_EMOJI or member.id not in trustedGroup:
			return
		if reaction.message.author.id == member.id:
			await reaction_requestAnswered(reaction, member, True, requests=requests, vectorstore=vectorstore)
			return
		await reaction_newOrUpdateRequest(reaction, member, requests=requests)
	# If it is on a request message...
	else:
		# ...and it's not one of the two accepted emojis, or not by the recipient, ignore
		if reaction.emoji not in {"✅", "❌"} or (record := requests[reaction.message]) is None or member.id != record["recipientID"]:
			return
		await reaction_requestAnswered(reaction, member, reaction.emoji == "✅", requests=requests, vectorstore=vectorstore)


bot.run(DISCORD_BOT_TOKEN.get_secret_value())