from langchain_groq import ChatGroq
from pydantic import SecretStr

from src.translations import AITexts
from Settings import LANGUAGE

class AI:
	_ai: ChatGroq
	_systemPrompt: str
	_maxInputCharacters: int | None
	def __init__(self, apiKey: SecretStr, systemPrompt: str, temperature: float = 0., maxInputCharacters: int | None = None) -> None:
		"""Initialization."""
		if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1: raise ValueError(AITexts.INVALID_TEMPERATURE[LANGUAGE].replace("[temperature]", f"{temperature}"))
		self._ai = ChatGroq(
			model="llama-3.1-8b-instant",
			temperature=temperature,
			api_key=apiKey
		)
		if not isinstance(systemPrompt, str) or not systemPrompt: raise ValueError(AITexts.INVALID_SYSTEM_PROMPT[LANGUAGE].replace("[prompt]", f"{systemPrompt}"))
		self._systemPrompt = systemPrompt
		if maxInputCharacters is not None:
			if not isinstance(maxInputCharacters, int): raise ValueError(AITexts.INVALID_SYSTEM_PROMPT[LANGUAGE].replace("[count]", f"{maxInputCharacters}"))
			if maxInputCharacters <= len(systemPrompt): raise ValueError(AITexts.MAX_CHARACTERS_TOO_SMALL[LANGUAGE].replace("[count]", f"{maxInputCharacters}").replace("[promptLength]", f"{len(systemPrompt)}"))
		self._maxInputCharacters = maxInputCharacters
	
	def query(self, query: str, context: str | None = None) -> str:
		"""Generates and returns an answer for the provided query and context."""
		systemPromptWithContext = self._systemPrompt + ("\n\n" + AITexts.CONTEXT_ADDITION[LANGUAGE].replace("[context]", f"{context}") if context is not None else "")
		messages = [
			("system", systemPromptWithContext),
			("human", query[:(min(self._maxInputCharacters - len(systemPromptWithContext), len(query)) if self._maxInputCharacters is not None else len(query))])
		]
		try:
			# response = ""
			# for chunk in self._ai.stream(messages):
			# 	if not chunk.content: continue
			# 	assert isinstance(chunk.content, str)
			# 	response += chunk.content
			# 	yield chunk.content
			response = self._ai.invoke(messages).content
		except Exception as e:
			return AITexts.QUERY_ERROR[LANGUAGE].replace("[error]", f"{e}")
		
		assert isinstance(response, str)
		# References, if added, would have to be handled outside of this function
		return response