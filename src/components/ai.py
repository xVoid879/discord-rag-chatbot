from langchain_groq import ChatGroq
from pydantic import SecretStr

from Settings import LANGUAGE
from src.components.output import Output
from src.translations import AITexts

class AI:
	_ai: ChatGroq
	_systemPrompt: str
	_maxInputCharacters: int | None
	_maxOutputCharacters: int | None
	def __init__(self, apiKey: SecretStr, systemPrompt: str, temperature: float = 0., maxInputCharacters: int | None = None, maxOutputCharacters: int | None = None) -> None:
		"""Initialization."""
		# API key
		if not isinstance(apiKey, SecretStr) or not apiKey: raise ValueError(AITexts.INVALID_API_KEY[LANGUAGE])
		# Temperature
		if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1: raise ValueError(AITexts.INVALID_TEMPERATURE[LANGUAGE].replace("[temperature]", f"{temperature}"))
		# Maximum output characters
		if maxOutputCharacters is not None and (not isinstance(maxOutputCharacters, int) or maxOutputCharacters <= 0): raise ValueError(AITexts.INVALID_MAX_OUTPUT_CHARACTERS_TYPE[LANGUAGE].replace("[count]", f"{maxOutputCharacters}"))
		self._maxOutputCharacters = maxOutputCharacters

		self._ai = ChatGroq(
			model="llama-3.1-8b-instant",
			temperature=temperature,
			api_key=apiKey,
			max_tokens=maxOutputCharacters
		)
		# System prompt
		if not isinstance(systemPrompt, str) or not systemPrompt: raise ValueError(AITexts.INVALID_SYSTEM_PROMPT[LANGUAGE].replace("[prompt]", f"{systemPrompt}"))
		self._systemPrompt = systemPrompt
		# Maximum input characters
		if maxInputCharacters is not None:
			if not isinstance(maxInputCharacters, int): raise ValueError(AITexts.INVALID_MAX_INPUT_CHARACTERS_TYPE[LANGUAGE].replace("[count]", f"{maxInputCharacters}"))
			if maxInputCharacters <= len(systemPrompt): raise ValueError(AITexts.MAX_CHARACTERS_TOO_SMALL[LANGUAGE].replace("[count]", f"{maxInputCharacters}").replace("[promptLength]", f"{len(systemPrompt)}"))
		self._maxInputCharacters = maxInputCharacters
	
	def query(self, query: str, context: str | None = None) -> str:
		"""Generates and returns an answer for the provided query and context."""
		systemPromptWithContext = self._systemPrompt + ("\n\n" + AITexts.CONTEXT_ADDITION[LANGUAGE].replace("[context]", f"{context}") if context is not None else "")
		messages = [
			("system", systemPromptWithContext),
			# Truncate query if necessary
			("human", query[:(min(self._maxInputCharacters - len(systemPromptWithContext), len(query)) if self._maxInputCharacters is not None else len(query))])
		]
		try:
			response = self._ai.invoke(messages).content
		except Exception as e:
			return AITexts.QUERY_ERROR[LANGUAGE].replace("[error]", f"{e}")
		
		assert isinstance(response, str)
		# Truncate response if necessary.
		# References are handled outside of this function.
		return Output.truncate(response, self._maxOutputCharacters) if self._maxOutputCharacters is not None else response