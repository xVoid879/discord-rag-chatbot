from discord import Intents
from discord.ext.commands import Bot, Context
from pydantic import SecretStr
from sys import argv

from Settings import *
from src.ai import AI
from src.cache import Cache
from src.cooldown import Cooldown
from src.vectorstore import Vectorstore

if len(argv) < 2: raise RuntimeError("No Discord bot token provided (must be 1st argument).")
DISCORD_BOT_TOKEN = SecretStr(argv[1])
if len(argv) < 3: raise RuntimeError("No Groq API key provided (must be 2nd argument).")
AI_API_KEY = SecretStr(argv[2])
PRIVILEGED_USER_IDS = set(int(id) for id in argv[3:])

intents = Intents.default()
intents.message_content = True
bot = Bot(command_prefix="->", intents=intents)

ai = AI(AI_API_KEY, AI_SYSTEM_PROMPT, AI_TEMPERATURE, AI_MAX_INPUT_CHARACTERS)
cooldown = Cooldown(COOLDOWN_DURATION, COOLDOWN_CHECK_INTERVAL, COOLDOWN_MAX_QUERIES_BEFORE_ACTIVATION) if COOLDOWN_DURATION is not None and COOLDOWN_DURATION > 0. else None
cache = Cache(CACHE_MAX_SIZE, CACHE_EXPIRATION_TIME, CACHE_SEMANTIC_SIMILARITY_THRESHOLD) if CACHE_MAX_SIZE > 0 else None
vectorstore = Vectorstore(VECTORSTORE_FILEPATH, VECTORSTORE_CONTEXT_RELEVANCE_THRESHOLD)

@bot.command()
async def ask(ctx: Context[Bot], *, query: str) -> None:
	"""Looks up and generates an answer for the provided query."""
	# Check cooldown
	if ctx.author.id in DISCORD_ID_BLACKLIST:
		await ctx.message.add_reaction("❌")
		return
	if cooldown is not None:
		if (remainingCooldown := cooldown.getRemainingTime()) > 0.:
			await ctx.send(COOLDOWN_MESSAGE + f" ({remainingCooldown:.2g} seconds remaining)", reference=ctx.message, mention_author=False)
			await ctx.message.add_reaction("❌")
			return
	# Check caches
	if cache is not None:
		if response := cache.getExactMatch(query):
			await ctx.send(response + f"\n-# Cached response. {AI_DISCLAIMER}", reference=ctx.message, mention_author=False)
			await ctx.message.add_reaction("✅")
			return
		if response := cache.getSemanticMatch(query):
			await ctx.send(response + f"\n-# Cached response. {AI_DISCLAIMER}", reference=ctx.message, mention_author=False)
			await ctx.message.add_reaction("✅")
			return
	# Retrieve context from vectorstore
	context = "\n- ".join(text for text, _ in vectorstore.query(query)) if vectorstore is not None else None
	# If context is required, and no context is found, return error
	if context:
		context = "- " + context
	elif AI_ERROR_IF_NO_CONTEXT:
		await ctx.send(AI_ERROR_IF_NO_CONTEXT, reference=ctx.message, mention_author=False)
		await ctx.message.add_reaction("✅")
		return

	# Retrieve AI response
	response = ai.query(query, context) if AI_ENABLE else "Here are the relevant messages in my corpus relating to your question:\n" + ("- None" if context is None else context)
	# Send message to user, and cache for future
	await ctx.send(response + f"\n-# {AI_DISCLAIMER}", reference=ctx.message, mention_author=False)
	await ctx.message.add_reaction("✅")
	if cache is not None:
		cache[query] = (response, cache.embed(query))


@bot.command()
async def addtext(ctx: Context[Bot], *texts: str) -> None:
	"""(Privileged command) Adds the provided texts to the vectorstore.
	   To avoid mistakes with forgetting quotation marks, at least one text must be 2+ words.
	   Quotation marks embedded in texts must be "escaped" by adding a backslash directly in front of them."""
	if ctx.author.id not in PRIVILEGED_USER_IDS or ctx.author.id in DISCORD_ID_BLACKLIST:
		await ctx.message.add_reaction("❌")
		return
	if vectorstore is None:
		await ctx.send(f"Error: No vectorstore exists to add the text{'' if len(texts) == 1 else 's'} to.", reference=ctx.message, mention_author=False)
		await ctx.message.add_reaction("❌")
		return
	if len([word for text in texts for word in text.split()]) == len(texts):
		await ctx.send(f"All texts received solely consisted of individual words. Make sure to wrap your texts in quotation marks.", reference=ctx.message, mention_author=False)
		await ctx.message.add_reaction("❌")
		return
	if (savedCount := vectorstore.add(texts)) < len(texts):
		await ctx.send(f"{len(texts) - savedCount} text{'' if len(texts) - savedCount == 1 else 's'} failed to be added.", reference=ctx.message, mention_author=False)
		await ctx.message.add_reaction("❌")
		return
	await ctx.message.add_reaction("✅")


# @bot.command()
# async def removetext(ctx: Context[Bot], *texts: str) -> None:
# 	"""(Privileged command) Adds the provided texts to the vectorstore.
# 	   To avoid mistakes with forgetting quotation marks, at least one text must be 2+ words.
# 	   Quotation marks embedded in texts must be "escaped" by adding a backslash directly in front of them."""
# 	if ctx.author.id not in PRIVILEGED_USER_IDS or ctx.author.id in DISCORD_ID_BLACKLIST:
# 		await ctx.message.add_reaction("❌")
# 		return
# 	if vectorstore is None:
# 		await ctx.send(f"Error: No vectorstore exists to add the text{'' if len(texts) == 1 else 's'} to.", reference=ctx.message, mention_author=False)
# 		await ctx.message.add_reaction("❌")
# 		return
# 	if len([word for text in texts for word in text.split()]) == len(texts):
# 		await ctx.send(f"All texts received solely consisted of individual words. Make sure to wrap your texts in quotation marks.", reference=ctx.message, mention_author=False)
# 		await ctx.message.add_reaction("❌")
# 		return
# 	if (savedCount := vectorstore.remove(texts)) < len(texts):
# 		await ctx.send(f"{len(texts) - savedCount} text{'' if len(texts) - savedCount == 1 else 's'} failed to be removed.", reference=ctx.message, mention_author=False)
# 		await ctx.message.add_reaction("❌")
# 		return
# 	await ctx.message.add_reaction("✅")


@bot.command()
async def save(ctx: Context[Bot], *, filepath: str | None = None):
	"""(Privileged command) Saves the vectorstore to the provided filepath, or the last-used filepath if none is provided."""
	if ctx.author.id not in PRIVILEGED_USER_IDS or ctx.author.id in DISCORD_ID_BLACKLIST:
		await ctx.message.add_reaction("❌")
		return
	if vectorstore is None:
		await ctx.send(f"Error: No vectorstore exists to save.", reference=ctx.message, mention_author=False)
		await ctx.message.add_reaction("❌")
		return
	if not vectorstore.save(filepath):
		await ctx.send(f"An error occurred while saving the vectorstore.", reference=ctx.message, mention_author=False)
		await ctx.message.add_reaction("❌")
		return
	await ctx.message.add_reaction("✅")


@bot.command()
async def load(ctx: Context[Bot], *, filepath: str | None = None):
	"""(Privileged command) Loads the vectorstore from the provided filepath, or the last-used filepath if none is provided."""
	global vectorstore
	if ctx.author.id not in PRIVILEGED_USER_IDS or ctx.author.id in DISCORD_ID_BLACKLIST:
		await ctx.message.add_reaction("❌")
		return
	if vectorstore is None:
		vectorstore = Vectorstore(filepath)
	if not vectorstore.load(filepath):
		await ctx.send(f"An error occurred while loading the vectorstore.", reference=ctx.message, mention_author=False)
		await ctx.message.add_reaction("❌")
		return
	await ctx.message.add_reaction("✅")

bot.run(DISCORD_BOT_TOKEN.get_secret_value())