from threading import Lock
from time import monotonic

class Cooldown:
	# TODO: Split up cooldown per server/per user
	_duration: float
	_checkInterval: float
	_maxMessagesBeforeCheck: int
	_messageTimes: list[float]
	_cooldownBeginningTimestamp: float | None
	_mutex: Lock

	def __init__(self, duration: float, checkInterval: float, maxMessagesBeforeCheck: int) -> None:
		"""Initialization."""
		if not isinstance(duration, (int, float)) or duration <= 0.: raise ValueError(f"Invalid cooldown duration provided: {duration}")
		self._duration = duration
		if not isinstance(checkInterval, (int, float)) or checkInterval <= 0.: raise ValueError(f"Invalid cooldown check period provided: {checkInterval}")
		self._checkInterval = checkInterval
		if not isinstance(maxMessagesBeforeCheck, int) or maxMessagesBeforeCheck <= 0: raise ValueError(f"Invalid maximum allowed messages before check provided: {maxMessagesBeforeCheck}")
		self._maxMessagesBeforeCheck = maxMessagesBeforeCheck
		self._messageTimes = []
		self._cooldownBeginningTimestamp = None
		self._mutex = Lock()

	def getRemainingTime(self) -> float:
		"""Returns the number of remaining seconds until the user can resume."""
		# Mutex to prevent race conditions
		self._mutex.acquire_lock()
		currentTimestamp = monotonic()
		# If a cooldown exists:
		if self._cooldownBeginningTimestamp is not None:
			# And the duration has already elapsed, no problem exists
			if currentTimestamp - self._cooldownBeginningTimestamp >= self._duration:
				self._cooldownBeginningTimestamp = None
				self._mutex.release_lock()
				return 0.
			# Case of duration not having elapsed falls through
		else:
			# Track last N message times. If < N messages have been sent or time between current and Nth message is above cooldown, no problem exists
			self._messageTimes = self._messageTimes[-self._maxMessagesBeforeCheck:] + [currentTimestamp]
			if (len(self._messageTimes) <= self._maxMessagesBeforeCheck or self._messageTimes[-1] - self._messageTimes[-self._maxMessagesBeforeCheck - 1] >= self._checkInterval):
				self._mutex.release_lock()
				return 0.
			# Set timestamp of cooldown beginning
			self._cooldownBeginningTimestamp = currentTimestamp

		# Return remaining time
		self._mutex.release_lock()
		return max(self._duration + self._cooldownBeginningTimestamp - currentTimestamp, 0.)
	
	def isBlocking(self) -> bool:
		"""Returns whether a cooldown is currently active."""
		return not self.getRemainingTime()