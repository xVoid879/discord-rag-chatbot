from langchain_groq import ChatGroq
from pydantic import SecretStr

class AI:
	_ai: ChatGroq
	_systemPrompt: str
	_maxInputCharacters: int | None
	def __init__(self, apiKey: SecretStr, systemPrompt: str, temperature: float = 0., maxInputCharacters: int | None = None) -> None:
		"""Initialization."""
		if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1: raise ValueError(f"Invalid temperature provided: {temperature}")
		self._ai = ChatGroq(
			model="llama-3.1-8b-instant",
			temperature=temperature,
			api_key=apiKey
		)
		if not isinstance(systemPrompt, str) or not systemPrompt: raise ValueError(f"Invalid system prompt provided: {systemPrompt}")
		self._systemPrompt = systemPrompt
		if maxInputCharacters is not None:
			if not isinstance(maxInputCharacters, int): raise ValueError(f"Invalid maximum input characters count provided: {maxInputCharacters}")
			if maxInputCharacters <= len(systemPrompt): raise ValueError(f"Maximum input characters is too small to pass any user prompts ({maxInputCharacters} vs. {len(systemPrompt)} characters excluding context).")
		self._maxInputCharacters = maxInputCharacters
	
	def query(self, query: str, context: str | None = None) -> str:
		"""Generates and returns an answer for the provided query and context."""
		systemPromptWithContext = self._systemPrompt + ("\n\nContext: " + context if context is not None else "")
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
			return f"Error generating response: {str(e)}"
		
		assert isinstance(response, str)
		# References, if added, would have to be handled outside of this function
		return response