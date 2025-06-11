# import faiss
# from fastembed import TextEmbedding
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
import os
from typing import Iterable

from src.components.output import Output
from src.components.saveableClass import SaveableClass

# EMBEDDING_MODEL = TextEmbedding()
EMBEDDING_MODEL = FastEmbedEmbeddings()
# embeddingDimension = list(EMBEDDING_MODEL.embed(""))[0].size

# TODO: Also store and retrieve messages' jump URLs as metadata
class Vectorstore(SaveableClass):
	# _vectorstore: faiss.IndexFlatL2
	_vectorstore: FAISS
	_minimumRelevance: float
	_segmentSize: int | None

	def __init__(self, filepath: str | None = None, minimumRelevance: float | None = None, segmentSize: int | None = None) -> None:
		"""Initialization."""
		super().__init__(filepath)
		if minimumRelevance is not None and (not isinstance(minimumRelevance, (int, float)) or minimumRelevance < 0. or minimumRelevance > 1.): raise ValueError(f"Invalid minimum relevance provided: {minimumRelevance}")
		self._minimumRelevance = 0. if minimumRelevance is None else minimumRelevance
		if segmentSize is not None and (not isinstance(segmentSize, int) or segmentSize <= 0): raise ValueError(f"Invalid segment size provided: {segmentSize}")
		self._segmentSize = segmentSize

		# self._vectorstore = faiss.read_index(filepath) if path else faiss.IndexFlatL2(embeddingDimension)
		if not self.load(filepath):
			self._vectorstore = FAISS.from_texts([""], EMBEDDING_MODEL)

	def query(self, query: str, maxResults: int = 4) -> list[tuple[str, float]]:
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
		allTexts = [segment for t in ([text] if isinstance(text, str) else list(text)) for segment in (Output.splitIntoSentences(t, self._segmentSize, True) if self._segmentSize is not None else [t]) ]
		self._vectorstore.add_texts(allTexts)
		return len(allTexts)
	
	def remove(self, text: str | Iterable[str]) -> int:
		"""Removes texts from the vectorstore. Returns the number of documents removed.
		Not yet implemented."""
		raise NotImplementedError
		# allTexts = [text] if isinstance(text, str) else list(text)
		# ...
		# return len(allTexts)
	
	def clear(self) -> None:
		raise NotImplementedError
	
	def save(self, filepath: str | None = None) -> bool:
		"""Saves the vectorstore to the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if (filepath := super().getFilepath(filepath)) is None: return False
		# faiss.write_index(self._vectorstore, filepath)
		self._vectorstore.save_local(os.path.dirname(filepath), os.path.splitext(os.path.basename(filepath))[0])
		return True
	
	def load(self, filepath: str | None = None) -> bool:
		"""Loads the vectorstore from the provided filepath, or the last-used filepath if none is provided. Returns whether it succeeded."""
		if (filepath := super().getFilepath(filepath)) is None: return False
		# self._vectorstore = faiss.read_index(filepath)
		self._vectorstore = FAISS.load_local(os.path.dirname(filepath), EMBEDDING_MODEL, os.path.splitext(os.path.basename(filepath))[0], allow_dangerous_deserialization=True)
		return True