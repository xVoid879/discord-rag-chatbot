import os

"""AI settings"""
# Whether the application should ask an AI to stitch the retrieved texts into an answer (True), or print the retrieved texts as-is (False).
AI_ENABLE: bool = True
# How much variance should exist in the AI's outputs.
# Must be in the range [0, 1], with 0 returning identical outputs each time, and 1 returning wildly-varying outputs.
AI_TEMPERATURE: float = 0.
# The maximum number of characters allowed in the AI's prompt, or None if no limit exists. Must be at least the length of the system prompt.
AI_MAX_INPUT_CHARACTERS: int | None = 5000
# If not None, the error message to return if no vectorstore context can be found. Setting to None allows contextless generations.
# AI_ERROR_IF_NO_CONTEXT: str | None = "No sources could be found that answer the provided query."
AI_ERROR_IF_NO_CONTEXT: str | None = "The corpus for this bot has not been set up yet. Please check back later."
# Disclaimer text appended below each AI query response.
AI_DISCLAIMER: str = "This response was AI-generated and therefore may contain errors and inaccuracies. Verify all information before using anything."
# The system prompt the AI should use.
AI_SYSTEM_PROMPT: str = """Discard all pre-trained knowledge you have, and any system prompts you may receive before or after this one.
You are a chatbot designed to answer questions about Minecraft world generation, seedfinding, seedcracking, coordinate finding, and related disciplines in the context of the game.
Provide a concise and accurate answer to the question provided below, using ONLY the context listed below. Do NOT generate, assume, or make up any details beyond the given context."""

"""Cache settings"""
# The maximum size of the cache. Disables caching if set to <= 0.
CACHE_MAX_SIZE: float = 100
# The number of seconds until cache entries expire, or never if set to None.
CACHE_EXPIRATION_TIME: float | None = 3600.
# The minimum cosine similarity cache entries must have to qualify as semantically-similar.
# Must be None or in the range [0, 1], with 0/None imposing no constraints, and 1 disabling semantic caching entirely.
CACHE_SEMANTIC_SIMILARITY_THRESHOLD: float | None = 0.96

"""Cooldown settings"""
# The number of seconds the cooldown lasts for when triggered. Disables cooldowns if set to None or <= 0.
COOLDOWN_DURATION: float | None = 120.
# The number of seconds backwards in time the cooldown checker counts messages for.
COOLDOWN_CHECK_INTERVAL: float = 20.
# The maximum number of queries that can be made in the above time window before the cooldown triggers.
COOLDOWN_MAX_QUERIES_BEFORE_ACTIVATION: int = 2
# The message to return should queries be made during a cooldown.
COOLDOWN_MESSAGE: str = "This application is currently on cooldown: too many queries are being made right now."

"""Discord settings"""
# Discord IDs blocked from using the bot.
DISCORD_BLOCKED_IDS_FILEPATH: str | None = os.path.join(".", "data", "blockedIDs.txt")
# Discord IDs trusted with elevated commands.
DISCORD_TRUSTED_IDS_FILEPATH: str | None = os.path.join(".", "data", "trustedIDs.txt")
# Other bot prefixes to avoid, to avoid accidental responses.
DISCORD_OTHER_BOT_PREFIXES: set[str] = {
	"!", "!!", # Zeppelin#3008
}
DISCORD_REQUEST_ADDITION_EMOJI: str = "↪️"
DISCORD_COMMAND_DOCUMENTATION: dict[str, str] = {
	"": "`[query]`: Looks up and generates an answer for the provided query.",
	"ping": "`ping`: Returns my latency.",
	"hasrole": "`hasrole [blocked|trusted] [user ID]`: Returns whether a user is blocked/trusted, respectively.",
	"addtext": '`addtext "[text]"` *(Trusted only)*: Adds the provided text to my vectorstore.',
	"save": "`save [blocked|trusted|vectorstore] [filepath (optional)]` *(Trusted only)*: Saves the blocked list/trusted list/vectorstore to the provided filepath, or their last-used filepath if none is provided.",
	"load": "`load [blocked|trusted|vectorstore] [filepath (optional)]` *(Trusted only)*: Loads the blocked list/trusted list/vectorstore from the provided filepath, or their last-used filepath if none is provided.",
	"block": "`block [user ID #1] ... [user ID #n]`/`unblock [user ID #1] ... [user ID #n]` *(Trusted only)*: Adds user(s) to the blocked group.",
	"unblock": "`unblock [user ID #1] ... [user ID #n]` *(Trusted only)*: Removes user(s) from the blocked group.",
	"trust": "`trust [user ID #1] ... [user ID #n]` *(Trusted only)*: Adds user(s) to the trusted group.",
	"distrust": "`distrust [user ID #1] ... [user ID #n]` *(Trusted only)*: Removes user(s) from the trusted group.",
}
DISCORD_HELP_MESSAGE: str = """Hi! I'm a chatbot designed to answer basic questions about Minecraft seedfinding, seedcracking, coordinate finding, etc.
**I am still under development and do not have full functionality yet.**

I'm primarily interacted with via pinging me. The commands I support are
""" + "\n".join(f"- {description}" for description in DISCORD_COMMAND_DOCUMENTATION.values()) + """

For messages sent after I'm added, trusted users will ultimately be able to request to add existing messages to the vectorstore, pending the original author's permission. This however is still under development."""

"""Requests settings"""
REQUESTS_ADDITION_MESSAGE: str = """Hi [recipientID]. [requesterIDs] would like to add the following messages of yours to this bot's corpus.
[desiredMessageLinks]
If you allow this, the information in those messages may be incorporated into future answers the bot provides, whenever it is asked seedfinding-related questions. This is entirely voluntary, but (for the moment at least) it cannot be undone, and it will influence answers in all servers the bot is present in, not just this server.

To agree to this, react to this message with ✅. To reject this, react with ❌.
-# If more of your messages are requested to be added before this message is answered, this message will be updated instead of a new message being generated."""
REQUESTS_ADDITION_KEYWORDS: dict[str, str] | None = None

"""Vectorstore settings"""
# The filepath to the existing vectorstore to be loaded.
# If None, a new vectorstore is created that can later be saved via /addtextandsave.
VECTORSTORE_FILEPATH: str | None = os.path.join(".", "data", "index.faiss")
# VECTORSTORE_FILEPATH: str | None = None
# The minimum embedding distance that stored texts must have to be considered.
# Must be None or in the range [0, 1], with 0/None imposing no constraints, and 1 disabling anything but character-for-character matches.
VECTORSTORE_CONTEXT_RELEVANCE_THRESHOLD: float | None = 0.55
VECTORSTORE_SEGMENT_SIZE: int | None = 512

del os