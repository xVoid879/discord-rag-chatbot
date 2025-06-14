from discord import Interaction, InteractionMessage, Message, WebhookMessage
from discord import Thread, StageChannel, TextChannel, VoiceChannel
from discord.ext.commands import Bot # type: ignore
from typing import overload

class Output:
	DISCORD_MESSAGE_CHARACTER_LIMIT: int = 2000
	DISCORD_DESCRIPTION_CHARACTER_LIMIT: int = 100

	@staticmethod
	async def getMessageFromURL(url: str, *, bot: Bot) -> Message | None:
		# Adapted from Stack Overflow: https://stackoverflow.com/a/63212069
		splitURL = url.split("/", maxsplit=7)
		if len(splitURL) < 7: return None
		try:
			channelID, messageID = int(splitURL[5]), int(splitURL[6])
		except ValueError: return None
		return (await channel.fetch_message(messageID)) if (channel := bot.get_channel(channelID)) is not None and isinstance(channel, (StageChannel, Thread, TextChannel, VoiceChannel)) else None

	@staticmethod
	def findSentenceEnd(text: str, minimumLength: int, desiredCharacterLimit: int = DISCORD_MESSAGE_CHARACTER_LIMIT) -> int:
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
	def splitIntoSentences(text: str, desiredCharacterLimit: int = DISCORD_MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False) -> list[str]:
		segments: list[str] = []
		minimumLength = int(0.2*desiredCharacterLimit)
		while len(text) > desiredCharacterLimit:
			i = Output.findSentenceEnd(text, minimumLength, desiredCharacterLimit)
			segments.append(text[:i])
			if overlapSentences:
				for i in range(int(i * 0.85), 1, -1):
					if text[i].isalnum() and text[i - 1].isspace(): break
			text = text[i:]
		return segments + [text]

	@staticmethod
	def truncate(text: str, desiredCharacterLimit: int = DISCORD_MESSAGE_CHARACTER_LIMIT) -> str:
		if not (splitText := Output.splitIntoSentences(text, desiredCharacterLimit - 1)): return ""
		return splitText[0] + ("…" if len(splitText) > 1 else "")

	@staticmethod
	@overload
	async def replyWithinCharacterLimit(message: Interaction, text: str, limit: int | None = DISCORD_MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False, ephemeral: bool = False) -> list[WebhookMessage]:
		raise NotImplementedError

	@staticmethod
	@overload
	async def replyWithinCharacterLimit(message: Message, text: str, limit: int | None = DISCORD_MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False) -> list[Message]:
		raise NotImplementedError

	@staticmethod
	async def replyWithinCharacterLimit(message: Interaction | Message, text: str, limit: int | None = DISCORD_MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False, ephemeral: bool = False) -> list[Message] | list[WebhookMessage]:
		if isinstance(message, Interaction) and not message.response.is_done(): await message.response.defer(ephemeral=ephemeral)
		segmentedText = Output.splitIntoSentences(text, limit, overlapSentences=overlapSentences) if limit is not None and limit > 0 else [text]
		sentMessages: list[Message | WebhookMessage] = []
		for segment in (s for s in segmentedText if s):
			sentMessages.append(
				await lastMessage.followup.send(segment, wait=True, ephemeral=ephemeral)
				if isinstance(lastMessage := sentMessages[-1] if sentMessages else message, Interaction)
				else await lastMessage.reply(segment, mention_author=False))
		return sentMessages
	
	@staticmethod
	@overload
	async def editWithinCharacterLimit(message: Interaction, text: str, limit: int | None = DISCORD_MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False, ephemeral: bool = False) -> list[InteractionMessage | WebhookMessage]:
		raise NotImplementedError

	@staticmethod
	@overload
	async def editWithinCharacterLimit(message: Message, text: str, limit: int | None = DISCORD_MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False) -> list[Message]:
		raise NotImplementedError

	@staticmethod
	async def editWithinCharacterLimit(message: Interaction | Message, text: str, limit: int | None = DISCORD_MESSAGE_CHARACTER_LIMIT, *, overlapSentences: bool = False, ephemeral: bool = False) -> list[Message] | list[InteractionMessage | WebhookMessage]:
		if isinstance(message, Interaction) and not message.response.is_done(): await message.response.defer(ephemeral=ephemeral)
		segmentedText = Output.splitIntoSentences(text, limit, overlapSentences=overlapSentences) if limit is not None and limit > 0 else [text]
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
			await message.add_reaction("✅")
			if text is None: return
		await Output.replyWithinCharacterLimit(message, text if text is not None else "✅")

	@staticmethod
	async def indicateFailure(message: Interaction | Message, error: str | None = None) -> None:
		if isinstance(message, Message):
			await message.add_reaction("❌")
			if error is None: return
		await Output.replyWithinCharacterLimit(message, error if error is not None else "A failure occurred.")