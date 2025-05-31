from discord import Message

def findSentenceEnd(text: str, minimumLength: int, desiredCharacterLimit: int) -> int:
    if desiredCharacterLimit <= 0: raise ValueError(f"Invalid desired character limit provided: {desiredCharacterLimit}")
    if len(text) < desiredCharacterLimit: return len(text)
    SENTENCE_SPLITTERS = {".", "!", "?", ")", "\n"}
    # Best-case scenario: end the segment at a terminating punctuation mark, immediately preceded by a non-whitespace character, and followed by whitespace.
    for i in range(desiredCharacterLimit, minimumLength + 1, -1):
        if text[i].isspace() and text[i - 1] in SENTENCE_SPLITTERS and not text[i - 2].isspace(): return i
    # Next-best: end the segment at a terminating punctuation mark, followed by whitespace.
    for i in range(desiredCharacterLimit, minimumLength + 1, -1):
        if text[i].isspace() and text[i - 1] in SENTENCE_SPLITTERS: return i
    # Third-best: end the segment at an alphanumeric character, followed by whitespace.
    for i in range(desiredCharacterLimit, minimumLength, -1):
        if text[i].isspace() and text[i - 1].isalnum(): return i
    # Third-best: end the segment at whitespace.
    for i in range(desiredCharacterLimit, minimumLength, -1):
        if text[i].isspace(): return i
    # Last-ditch: Just use the character limit
    return desiredCharacterLimit


def splitIntoSentences(text: str, desiredCharacterLimit: int, overlapSentences: bool = False) -> list[str]:
    segments: list[str] = []
    minimumLength = int(0.2*desiredCharacterLimit)
    while len(text) > desiredCharacterLimit:
        i = findSentenceEnd(text, minimumLength, desiredCharacterLimit)
        segments.append(text[:i])
        if overlapSentences:
            for i in range(int(i * 0.85), 1, -1):
                if text[i].isalnum() and text[i - 1].isspace(): break
        text = text[i:]
    return segments + [text]


async def replyWithinCharacterLimit(message: Message, text: str, limit: int | None = None, overlapSentences: bool = False) -> Message:
    brokenText = splitIntoSentences(text, limit, overlapSentences) if limit is not None and limit > 0 else [text]
    for segment in brokenText:
        lastMessage = await message.reply(segment, mention_author=False)
    #type: ignore
    return lastMessage