from cachetools import TTLCache
from fastembed import TextEmbedding
from fastembed.common.types import NumpyArray
from math import sqrt
from numpy import ndarray

from src.translations import CacheTexts
from Settings import LANGUAGE

class Cache:
	_cache: TTLCache[str, tuple[str, NumpyArray]] # query: (response, query embedding)
	_embeddingModel: TextEmbedding
	_semanticSimilarityThreshold: float

	def __init__(self, maxSize: float, expirationTime: float | None = None, semanticSimilarityThreshold: float | None = 0.) -> None:
		"""Initialization."""
		if not isinstance(maxSize, (int, float)) or maxSize <= 0.: raise ValueError(CacheTexts.INVALID_MAX_SIZE[LANGUAGE].replace("[size]", f"{maxSize}"))
		if expirationTime is not None and (not isinstance(expirationTime, (int, float)) or expirationTime <= 0.): raise ValueError(CacheTexts.INVALID_EXPIRATION_TIME[LANGUAGE].replace("[time]", f"{expirationTime}"))
		self._cache = TTLCache(maxSize, float("inf") if expirationTime is None else expirationTime)
		self._embeddingModel = TextEmbedding()
		if semanticSimilarityThreshold is not None and (not isinstance(semanticSimilarityThreshold, (int, float)) or semanticSimilarityThreshold < 0. or semanticSimilarityThreshold > 1.): raise ValueError(CacheTexts.INVALID_SIMILARITY_THRESHOLD[LANGUAGE].replace("[threshold]", f"{semanticSimilarityThreshold}"))
		self._semanticSimilarityThreshold = 0. if semanticSimilarityThreshold is None else semanticSimilarityThreshold

	def __setitem__(self, key: str, value: tuple[str, NumpyArray]) -> None:
		"""Associates the provided key to the provided value in the cache."""
		if not isinstance(key, str): raise ValueError(CacheTexts.INVALID_KEY[LANGUAGE].replace("[key]", f"{key}"))
		if not isinstance(value, tuple) or len(value) != 2 or not isinstance(value[0], str) or not isinstance(value[1], ndarray): raise ValueError(CacheTexts.INVALID_VALUE[LANGUAGE].replace("[value]", f"{value}"))
		self._cache.__setitem__(key, value)

	@staticmethod
	def cosineSimilarity(vectorA: NumpyArray, vectorB: NumpyArray) -> float:
		"""Calculates the cosine similarity of the two provided vectors (in the range [0, 1])."""
		squaredNormA: float = (vectorA*vectorA).sum()
		squaredNormB: float = (vectorB*vectorB).sum()
		return (vectorA*vectorB).sum() / (sqrt(squaredNormA) * sqrt(squaredNormB)) if squaredNormA and squaredNormB else 0.

	def embed(self, text: str) -> NumpyArray:
		"""Constructs the embedding for the provided text."""
		# If only one text is embedded, FastEmbed returns a generator producing a single element, so we discard the generator.
		return list(self._embeddingModel.embed(text))[0]

	def getExactMatch(self, query: str) -> str | None:
		"""Queries the cache for an exact match. Returns None if not found."""
		return self._cache[query][0] if query in self._cache else None

	def getSemanticMatch(self, query: str) -> str | None:
		"""Queries the cache for the highest semantic match at or above the registered threshold. Returns None if none found."""
		if self._semanticSimilarityThreshold >= 1.:
			return None
		inputEmbedding = self.embed(query)
		bestMatch = None
		highestSimilarity = 0.
		for cachedAnswer, cachedEmbedding in self._cache.values():
			if (similarity := self.cosineSimilarity(inputEmbedding, cachedEmbedding)) <= highestSimilarity: continue
			highestSimilarity = similarity
			bestMatch = cachedAnswer
		return bestMatch if highestSimilarity >= self._semanticSimilarityThreshold else None
	
	def clear(self) -> None:
		self._cache.clear()