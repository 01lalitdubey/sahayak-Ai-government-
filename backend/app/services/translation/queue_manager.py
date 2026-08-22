import asyncio
import time
from typing import Dict, Any, List, Optional
import uuid

from app.models.enums import TranslationJobStatusEnum

class QueueState:
    def __init__(self):
        self.job_id: Optional[uuid.UUID] = None
        self.status: TranslationJobStatusEnum = TranslationJobStatusEnum.PENDING
        self.total_records: int = 0
        self.processed_records: int = 0
        self.failed_records: int = 0
        self.start_time: Optional[float] = None
        self.paused_time: float = 0
        self._last_pause_stamp: Optional[float] = None
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.current_languages: set = set()
        self.errors: List[dict] = []

    def get_speed(self) -> float:
        if not self.start_time or self.processed_records == 0:
            return 0.0
        
        active_time = time.time() - self.start_time - self.paused_time
        if self.status in [TranslationJobStatusEnum.PAUSED, TranslationJobStatusEnum.CANCELLED]:
            if self._last_pause_stamp:
                active_time = self._last_pause_stamp - self.start_time - self.paused_time

        if active_time <= 0:
            return 0.0
        return self.processed_records / active_time

    def get_eta(self) -> float:
        speed = self.get_speed()
        if speed <= 0:
            return 0.0
        remaining = self.total_records - self.processed_records - self.failed_records
        return remaining / speed

class TranslationQueueManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._state = QueueState()
        return cls._instance

    @property
    def state(self) -> QueueState:
        return self._instance._state

    def reset(self):
        self._state = QueueState()

    def pause(self):
        if self.state.status == TranslationJobStatusEnum.RUNNING:
            self.state.status = TranslationJobStatusEnum.PAUSED
            self.state._last_pause_stamp = time.time()

    def resume(self):
        if self.state.status == TranslationJobStatusEnum.PAUSED:
            self.state.status = TranslationJobStatusEnum.RUNNING
            if self.state._last_pause_stamp:
                self.state.paused_time += time.time() - self.state._last_pause_stamp
                self.state._last_pause_stamp = None

    def cancel(self):
        self.state.status = TranslationJobStatusEnum.CANCELLED
        # Clear queue to stop workers
        while not self.state.queue.empty():
            try:
                self.state.queue.get_nowait()
                self.state.queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        for w in self.state.workers:
            if not w.done():
                w.cancel()

    def is_running(self) -> bool:
        return self.state.status == TranslationJobStatusEnum.RUNNING

queue_manager = TranslationQueueManager()
