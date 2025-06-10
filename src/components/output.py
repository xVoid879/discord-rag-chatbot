from discord import Message

class Output:
	MAX_DISCORD_CHARACTER_LIMIT: int = 2000

	@staticmethod
	def findSentenceEnd(text: str, minimumLength: int, desiredCharacterLimit: int = MAX_DISCORD_CHARACTER_LIMIT) -> int:
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
	def splitIntoSentences(text: str, desiredCharacterLimit: int = MAX_DISCORD_CHARACTER_LIMIT, overlapSentences: bool = False) -> list[str]:
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
	async def replyWithinCharacterLimit(message: Message, text: str, limit: int | None = MAX_DISCORD_CHARACTER_LIMIT, overlapSentences: bool = False) -> list[Message]:
		brokenText = Output.splitIntoSentences(text, limit, overlapSentences) if limit is not None and limit > 0 else [text]
		return [await message.reply(segment, mention_author=False) for segment in brokenText if segment]
	
	@staticmethod
	async def editWithinCharacterLimit(message: Message, text: str, limit: int | None = MAX_DISCORD_CHARACTER_LIMIT, overlapSentences: bool = False) -> list[Message]:
		brokenText = Output.splitIntoSentences(text, limit, overlapSentences) if limit is not None and limit > 0 else [text]
		if not brokenText: return []
		await message.edit(content=brokenText[0])
		return [message] + [await message.reply(segment, mention_author=False) for segment in brokenText[1:] if segment]