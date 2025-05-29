# import faiss
# from fastembed import TextEmbedding
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
import os
from typing import Iterable

# EMBEDDING_MODEL = TextEmbedding()
EMBEDDING_MODEL = FastEmbedEmbeddings()
# embeddingDimension = list(EMBEDDING_MODEL.embed(""))[0].size

class Vectorstore:
	# _vectorstore: faiss.IndexFlatL2
	_vectorstore: FAISS
	_minimumRelevance: float
	_filepath: str | None

	def __init__(self, filepath: str | None = None, minimumRelevance: float | None = None) -> None:
		"""Initialization."""
		if filepath is not None and (not isinstance(filepath, str) or not os.path.isfile(filepath)): raise RuntimeError(f"Invalid or nonexistent path provided: {filepath}")
		self._filepath = filepath
		if minimumRelevance is not None and (not isinstance(minimumRelevance, (int, float)) or minimumRelevance < 0. or minimumRelevance > 1.): raise ValueError(f"Invalid minimum relevance provided: {minimumRelevance}")
		self._minimumRelevance = 0. if minimumRelevance is None else minimumRelevance

		# self._vectorstore = faiss.read_index(filepath) if path else faiss.IndexFlatL2(embeddingDimension)
		if not self.load(filepath):
			self._vectorstore = FAISS.from_texts([""], EMBEDDING_MODEL)

	def query(self, query: str, maxResults: int = 5) -> list[tuple[str, float]]:
		"""Returns the most relevant results (text + score pairs) for the provided query, at or above the originally-specified relevance threshold."""
		# embedding = list(EMBEDDING_MODEL.embed(query))[0]
		# scores, indices = self._vectorstore.search(embedding, maxResults)
		# ...
		return sorted(((text.page_content, score) for text, score in self._vectorstore.similarity_search_with_relevance_scores(query, maxResults, score_threshold=self._minimumRelevance)), key=lambda textAndScore: -textAndScore[1]) # Negative key preserves order of equally-scored texts, which reverse=True would invert
	
	def add(self, text: str | Iterable[str]) -> int:
		"""Adds texts to the vectorstore. Returns the number of documents added."""
		# embedding = list(EMBEDDING_MODEL.embed(text))[0]
		# self._vectorstore.add(embedding)
		# ...?
		allTexts = [text] if isinstance(text, str) else list(text)
		self._vectorstore.add_texts(allTexts)
		return len(allTexts)
	
	# def remove(self, text: str | Iterable[str]) -> int:
	# 	"""Removes texts from the vectorstore. Returns the number of documents removed."""
	# 	allTexts = [text] if isinstance(text, str) else list(text)
	# 	...
	# 	return len(allTexts)
	
	def save(self, filepath: str | None = None) -> bool:
		"""Saves the vectorstore to the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if not filepath:
			if not self._filepath: return False # No saved filepath exists
			filepath = self._filepath # Otherwise use saved filepath
		elif not self._filepath:
			self._filepath = filepath
		os.makedirs(os.path.dirname(filepath), exist_ok=True)
		# faiss.write_index(self._vectorstore, filepath)
		self._vectorstore.save_local(os.path.dirname(filepath), os.path.splitext(os.path.basename(filepath))[0])
		return True
	
	def load(self, filepath: str | None = None) -> bool:
		"""Loads the vectorstore from the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if not filepath:
			if not self._filepath: return False # No saved filepath exists
			filepath = self._filepath # Otherwise use saved filepath
		if not os.path.isfile(filepath): return False
		if not self._filepath:
			self._filepath = filepath
		# self._vectorstore = faiss.read_index(filepath)
		self._vectorstore = FAISS.load_local(os.path.dirname(filepath), EMBEDDING_MODEL, os.path.splitext(os.path.basename(filepath))[0], allow_dangerous_deserialization=True)
		return True