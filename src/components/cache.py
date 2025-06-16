from cachetools import TTLCache
from fastembed import TextEmbedding
from fastembed.common.types import NumpyArray
from math import sqrt
from numpy import ndarray
from pickle import dump, load

from Settings import LANGUAGE
from src.components.saveableClass import SaveableClass
from Translations import CacheTexts

# TODO: Is there a way to save/load the cache (and by extension the Numpy arrays) without resorting to possibly-vulnerable Pickle serialization/deserialization?
class Cache(SaveableClass):
	_cache: TTLCache[str, tuple[str, NumpyArray]] | None # query: (response, query embedding)
	_embeddingModel: TextEmbedding
	_semanticSimilarityThreshold: float

	def __init__(self, maxSize: float, expirationTime: float | None = None, semanticSimilarityThreshold: float | None = 0., filepath: str | None = None) -> None:
		"""Initialization."""
		# Filepath
		super().__init__(filepath)
		# Embedding model
		self._embeddingModel = TextEmbedding()
		# Semantic threshold
		if semanticSimilarityThreshold is not None and (not isinstance(semanticSimilarityThreshold, (int, float)) or semanticSimilarityThreshold < 0. or semanticSimilarityThreshold > 1.): raise ValueError(CacheTexts.INVALID_SIMILARITY_THRESHOLD[LANGUAGE].replace("[threshold]", f"{semanticSimilarityThreshold}"))
		self._semanticSimilarityThreshold = 0. if semanticSimilarityThreshold is None else semanticSimilarityThreshold

		if not self.load(filepath):
			# Max size
			if not isinstance(maxSize, (int, float)) or maxSize < 0.: raise ValueError(CacheTexts.INVALID_MAX_SIZE[LANGUAGE].replace("[size]", f"{maxSize}"))
			# Expiration time
			if expirationTime is not None and (not isinstance(expirationTime, (int, float)) or expirationTime < 0.): raise ValueError(CacheTexts.INVALID_EXPIRATION_TIME[LANGUAGE].replace("[time]", f"{expirationTime}"))
			self._cache = TTLCache(maxSize, float("inf") if expirationTime is None else expirationTime) if maxSize > 0. and (expirationTime is None or expirationTime > 0.) else None

	def __len__(self) -> int:
		"""Returns the number of entries currently in the cache."""
		return len(self._cache) if self._cache is not None else 0

	def __setitem__(self, key: str, value: tuple[str, NumpyArray]) -> None:
		"""Associates the provided key to the provided value in the cache."""
		# Verify key type
		if not isinstance(key, str): raise ValueError(CacheTexts.INVALID_KEY[LANGUAGE].replace("[key]", f"{key}"))
		# Verify value type
		if not isinstance(value, tuple) or len(value) != 2 or not isinstance(value[0], str) or not isinstance(value[1], ndarray): raise ValueError(CacheTexts.INVALID_VALUE[LANGUAGE].replace("[value]", f"{value}"))
		if self._cache is None: return
		self._cache[key] = value

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
		return self._cache[query][0] if self._cache is not None and query in self._cache else None

	def getSemanticMatch(self, query: str) -> str | None:
		"""Queries the cache for the highest semantic match at or above the registered threshold. Returns None if none found."""
		if self._cache is None or self._semanticSimilarityThreshold >= 1.:
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
		"""Clears the cache."""
		if self._cache is None: return
		self._cache.clear()

	def save(self, filepath: str | None = None) -> bool:
		"""Saves the requests list to the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if (filepath := super().getFilepath(filepath)) is None: return False
		with open(filepath, "wb") as f: dump(self._cache, f)
		return True
	
	def load(self, filepath: str | None = None) -> bool:
		"""Loads the requests list from the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if (filepath := super().getFilepath(filepath)) is None: return False
		with open(filepath, "rb") as f: self._cache = load(f)
		return True