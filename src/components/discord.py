from discord import Interaction, InteractionMessage, Message, StageChannel, TextChannel, Thread, VoiceChannel, WebhookMessage
from discord.abc import Snowflake
from discord.ext.commands import Bot # type: ignore
from typing import overload

class Discord:
	MESSAGE_CHARACTER_LIMIT: int = 2000
	DESCRIPTION_CHARACTER_LIMIT: int = 100

	@staticmethod
	async def getMessage(url: str, *, bot: Bot) -> Message | None:
		"""Attempts to retrieve a message from a URL, provided the bot is able to see said message.
		Warning: This consumes an API call."""
		# Adapted from Stack Overflow: https://stackoverflow.com/a/63212069
		# Standard format is https: / / www.discord.com / channels / [server ID] / [channel ID] / [message ID]
		splitURL = url.split("/", maxsplit=7)
		if len(splitURL) < 7: return None
		try:
			channelID, messageID = int(splitURL[5]), int(splitURL[6])
		except ValueError: return None
		return (await channel.fetch_message(messageID)) if (channel := bot.get_channel(channelID)) is not None and isinstance(channel, (StageChannel, Thread, TextChannel, VoiceChannel)) else None
	
	@staticmethod
	async def convertToMessage(obj: str | Message, *, bot: Bot) -> Message | None:
		return await Discord.getMessage(obj, bot=bot) if isinstance(obj, str) else obj

	@staticmethod
	def findSentenceEnd(text: str, minimumLength: int, desiredCharacterLimit: int = MESSAGE_CHARACTER_LIMIT) -> int:
		"""Attempts to return the index after the end of the last complete sentence in the text."""
		if desiredCharacterLimit <= 0: raise ValueError(f"Invalid desired character limit provided: {desiredCharacterLimit}")
		if len(text) < desiredCharacterLimit: return len(text)
		SENTENCE_ENDING_CHARACTERS = {".", "!", "?", ")", "\n"}
		# Best-case scenario: end the segment at a terminating punctuation mark, immediately preceded by a non-whitespace character, and followed by whitespace.
		for i in range(desiredCharacterLimit, minimumLength + 1, -1):
			if text[i].isspace() and text[i - 1] in SENTENCE_ENDING_CHARACTERS and not text[i - 2].isspace(): return i
		# Next-best: end the segment at a terminating punctuation mark, followed by whitespace.
		for i in range(desiredCharacterLimit, minimumLength + 1, -1):
			if text[i].isspace() and text[i - 1] in SENTENCE_ENDING_CHARACTERS: return i
		# Third-best: end the segment at an alphanumeric character, followed by whitespace.
		for i in range(desiredCharacterLimit, minimumLength, -1):
			if text[i].isspace() and text[i - 1].isalnum(): return i
		# Fourth-best: end the segment at whitespace.
		for i in range(desiredCharacterLimit, minimumLength, -1):
			if text[i].isspace(): return i
		# Last-ditch: Just use the character limit
		return desiredCharacterLimit

	@staticmethod
	def splitIntoSentences(text: str, desiredCharacterLimit: int = MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False) -> list[str]:
		"""Splits the provided text into multiple segments, based on the provided desired character limit per segment."""
		segments: list[str] = []
		minimumLength = int(0.2*desiredCharacterLimit)
		while len(text) > desiredCharacterLimit:
			i = Discord.findSentenceEnd(text, minimumLength, desiredCharacterLimit)
			segments.append(text[:i])
			if overlapSentences:
				for i in range(int(i * 0.85), 1, -1):
					if text[i].isalnum() and text[i - 1].isspace(): break
			text = text[i:]
		return segments + [text]

	@staticmethod
	def truncate(text: str, desiredCharacterLimit: int = MESSAGE_CHARACTER_LIMIT) -> str:
		if not (splitText := Discord.splitIntoSentences(text, desiredCharacterLimit - 1)): return ""
		return splitText[0] + ("…" if len(splitText) > 1 else "")

	@staticmethod
	async def tryAddReaction(source: Message, emoji: str) -> bool:
		try:
			await source.add_reaction(emoji)
			return True
		except Exception as e:
			await Discord.replyWithinCharacterLimit(source, f"{e}")
			return False
		
	@staticmethod
	async def tryRemoveReaction(source: Message, emoji: str, member: Snowflake) -> bool:
		try:
			await source.remove_reaction(emoji, member)
			return True
		except Exception as e:
			await Discord.replyWithinCharacterLimit(source, f"{e}")
			return False

	@staticmethod
	@overload
	async def replyWithinCharacterLimit(message: Interaction, text: str, limit: int | None = MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False, ephemeral: bool = False) -> list[WebhookMessage]:
		raise NotImplementedError

	@staticmethod
	@overload
	async def replyWithinCharacterLimit(message: Message, text: str, limit: int | None = MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False) -> list[Message]:
		raise NotImplementedError

	@staticmethod
	async def replyWithinCharacterLimit(message: Interaction | Message, text: str, limit: int | None = MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False, ephemeral: bool = False) -> list[Message] | list[WebhookMessage]:
		if isinstance(message, Interaction) and not message.response.is_done(): await message.response.defer(ephemeral=ephemeral)
		segmentedText = Discord.splitIntoSentences(text, limit, overlapSentences=overlapSentences) if limit is not None and limit > 0 else [text]
		sentMessages: list[Message | WebhookMessage] = []
		for segment in (s for s in segmentedText if s):
			sentMessages.append(
				await lastMessage.followup.send(segment, wait=True, ephemeral=ephemeral)
				if isinstance(lastMessage := sentMessages[-1] if sentMessages else message, Interaction)
				else await lastMessage.reply(segment, mention_author=False))
		return sentMessages
	
	@staticmethod
	@overload
	async def editWithinCharacterLimit(message: Interaction, text: str, limit: int | None = MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False, ephemeral: bool = False) -> list[InteractionMessage | WebhookMessage]:
		raise NotImplementedError

	@staticmethod
	@overload
	async def editWithinCharacterLimit(message: Message, text: str, limit: int | None = MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False) -> list[Message]:
		raise NotImplementedError

	@staticmethod
	async def editWithinCharacterLimit(message: Interaction | Message, text: str, limit: int | None = MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False, ephemeral: bool = False) -> list[Message] | list[InteractionMessage | WebhookMessage]:
		if isinstance(message, Interaction) and not message.response.is_done(): await message.response.defer(ephemeral=ephemeral)
		segmentedText = Discord.splitIntoSentences(text, limit, overlapSentences=overlapSentences) if limit is not None and limit > 0 else [text]
		if not segmentedText: return []
		editedMessage = await message.edit_original_response(content=segmentedText[0]) if isinstance(message, Interaction) else await message.edit(content=segmentedText[0])
		sentMessages: list[InteractionMessage | Message | WebhookMessage] = [editedMessage]
		for segment in (s for s in segmentedText[1:] if s):
			sentMessages.append(
				await lastMessage.followup.send(segment, wait=True, ephemeral=ephemeral)
				if isinstance(lastMessage := sentMessages[-1] if sentMessages else message, Interaction)
				else await lastMessage.reply(segment, mention_author=False))
		return sentMessages
	
	@staticmethod
	async def indicateSuccess(message: Interaction | Message, text: str | None = None) -> None:
		if isinstance(message, Message):
			await Discord.tryAddReaction(message, "✅")
			if text is None: return
		await Discord.replyWithinCharacterLimit(message, text if text is not None else "✅")

	@staticmethod
	async def indicateFailure(message: Interaction | Message, error: str | None = None) -> None:
		if isinstance(message, Message):
			await Discord.tryAddReaction(message, "❌")
			if error is None: return
		await Discord.replyWithinCharacterLimit(message, error if error is not None else "A failure occurred.")