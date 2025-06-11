import os
from src.translations import SupportedLanguages

LANGUAGE: SupportedLanguages = "English"

"""AI settings"""
# How much variance should exist in the AI's outputs.
# Must be in the range [0, 1], with 0 returning identical outputs each time, and 1 returning wildly-varying outputs.
AI_TEMPERATURE: float = 0.
# The maximum number of characters allowed in the AI's prompt, or None if no limit exists. Must be at least the length of the system prompt.
AI_MAX_INPUT_CHARACTERS: int | None = 5000
# Whether the bot should abort and return an error message if no vectorstore context can be found.
# Outside of highly-controlled environments, it is highly recommended this be set to True.
AI_REQUIRE_CONTEXT: bool = True
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
# COOLDOWN_DURATION: float | None = 30.
COOLDOWN_DURATION: float | None = None
# The number of seconds backwards in time the cooldown checker counts messages for.
COOLDOWN_CHECK_INTERVAL: float = 20.
# The maximum number of queries that can be made in the above time window before the cooldown triggers.
COOLDOWN_MAX_QUERIES_BEFORE_ACTIVATION: int = 2

"""Discord settings"""
# Discord IDs blocked from using the bot.
DISCORD_BLOCKED_IDS_FILEPATH: str | None = os.path.join(".", "data", "blockedIDs.txt")
# Discord IDs trusted with elevated commands.
DISCORD_TRUSTED_IDS_FILEPATH: str | None = os.path.join(".", "data", "trustedIDs.txt")
# Discord IDs permitting all of their messages to be added without requesting individually each time.
DISCORD_PERMITTING_IDS_FILEPATH: str | None = os.path.join(".", "data", "permittingIDs.txt")
# Other bot prefixes to avoid, to avoid accidental responses.
DISCORD_OTHER_BOT_PREFIXES: set[str] = {
	"!", "!!", # Zeppelin#3008
}
DISCORD_REQUEST_ADDITION_EMOJI: str = "↪️"
DISCORD_COMMAND_DOCUMENTATION: dict[str, str] = {
	"": "`[query]`: Looks up and generates an answer for the provided query.",
	"help": "`help`: Prints my purpose and list of commands.",
	"ping": "`ping`: Returns my latency.",
	"hasrole": "`hasrole [blocked|permitting|trusted] [user ID]`: Returns whether a user is blocked/trusted, respectively.",
	"permit": "`permit`: Permits trusted users to add your messages to my corpus without individually requesting permission.",
	"revoke": "`revoke`: Revokes your permission for trusted users to add your messages without individually requesting permission.",
	"addtext": '`addtext "[text]"` *(Trusted only)*: Adds the provided text to my corpus.',
	"clear": "`clear [blocked|cache|permitting|trusted]` *(Trusted only)*: Clears the provided group/cache.",
	"save": "`save [blocked|permitting|trusted|vectorstore] [filepath (optional)]` *(Trusted only)*: Saves the blocked list/trusted list/permitting list/corpus to the provided filepath, or their last-used filepath if none is provided.",
	"load": "`load [blocked|permitting|trusted|vectorstore] [filepath (optional)]` *(Trusted only)*: Loads the blocked list/trusted list/permitting list/corpus from the provided filepath, or their last-used filepath if none is provided.",
	"block": "`block [user ID #1] ... [user ID #n]` *(Trusted only)*: Adds user(s) to the blocked group.",
	"unblock": "`unblock [user ID #1] ... [user ID #n]` *(Trusted only)*: Removes user(s) from the blocked group.",
	"trust": "`trust [user ID #1] ... [user ID #n]` *(Trusted only)*: Adds user(s) to the trusted group.",
	"distrust": "`distrust [user ID #1] ... [user ID #n]` *(Trusted only)*: Removes user(s) from the trusted group.",
}

"""Requests settings"""
REQUESTS_ADDITION_KEYWORDS: dict[str, str] | None = None

"""Vectorstore settings"""
# The filepath to the existing vectorstore to be loaded.
# If None, a new vectorstore is created that can later be saved via /addtextandsave.
VECTORSTORE_FILEPATH: str | None = os.path.join(".", "data", "index.faiss")
# VECTORSTORE_FILEPATH: str | None = None
# The minimum embedding distance that stored texts must have to be considered.
# Must be None or in the range [0, 1], with 0/None imposing no constraints, and 1 disabling anything but character-for-character matches.
VECTORSTORE_CONTEXT_RELEVANCE_THRESHOLD: float | None = 0.6
VECTORSTORE_SEGMENT_SIZE: int | None = 512

del os