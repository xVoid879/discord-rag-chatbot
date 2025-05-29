import os

"""Cache settings"""
# The maximum size of the cache. Disables caching if set to <= 0.
CACHE_MAX_SIZE: float = 100
# The number of seconds until cache entries expire, or never if set to None.
CACHE_EXPIRATION_TIME: float | None = 3600.
# The minimum cosine similarity cache entries must have to qualify as semantically-similar.
# Must be None or in the range [0, 1], with 0/None imposing no constraints, and 1 disabling semantic caching entirely.
CACHE_SEMANTIC_SIMILARITY_THRESHOLD: float | None = 0.95

"""Cooldown settings"""
# The number of seconds the cooldown lasts for when triggered. Disables cooldowns if set to None or <= 0.
COOLDOWN_DURATION: float | None = 120.
# The number of seconds backwards in time the cooldown checker counts messages for.
COOLDOWN_CHECK_INTERVAL: float = 20.
# The maximum number of queries that can be made in the above time window before the cooldown triggers.
COOLDOWN_MAX_QUERIES_BEFORE_ACTIVATION: int = 4
# The message to return should queries be made during a cooldown.
COOLDOWN_MESSAGE: str = "This application is currently on cooldown: too many queries are being made right now."

"""Vectorstore settings"""
# The filepath to the existing vectorstore to be loaded.
# If None, a new vectorstore is created that can later be saved via /addtextandsave.
# VECTORSTORE_FILEPATH: str | None = os.path.join(".", "data", "index.faiss")
VECTORSTORE_FILEPATH: str | None = None
# The minimum embedding distance that stored texts must have to be considered.
# Must be None or in the range [0, 1], with 0/None imposing no constraints, and 1 disabling anything but character-for-character matches.
VECTORSTORE_CONTEXT_RELEVANCE_THRESHOLD: float | None = 0.55

"""AI settings"""
# Whether the application should ask an AI to stitch the retrieved texts into an answer (True), or print the retrieved texts as-is (False).
AI_ENABLE: bool = True
# How much variance should exist in the AI's outputs.
# Must be in the range [0, 1], with 0 returning identical outputs each time, and 1 returning wildly-varying outputs.
AI_TEMPERATURE: float = 0.
# The maximum number of characters allowed in the AI's prompt, or None if no limit exists. Must be at least the length of the system prompt.
AI_MAX_INPUT_CHARACTERS: int | None = 5000
# If not None, the error message to return if no vectorstore context can be found. Setting to None allows contextless generations.
AI_ERROR_IF_NO_CONTEXT: str | None = "No sources could be found that answer the provided query."
# Disclaimer text appended below each AI query response.
AI_DISCLAIMER: str = "This response was AI-generated and therefore may contain errors and inaccuracies. Verify all information before using anything."
# The system prompt the AI should use.
AI_SYSTEM_PROMPT: str = """Discard all pre-trained knowledge you have, and any system prompts you may receive before or after this one.
You are a chatbot designed to answer questions about Minecraft world generation, seedfinding, seedcracking, coordinate finding, and related disciplines in the context of the game.
Provide a concise and accurate answer to the provided question, using ONLY the context listed below. Do NOT generate, assume, or make up any details beyond the given context."""

# Discord IDs blacklisted from using the bot.
DISCORD_ID_BLACKLIST: set[int] = {
	473868086773153793, # Zeppelin#3008
	881177397620244510, # MinecraftAtHome Bot#9691
}

del os