"""Background worker for running the search pipeline off the main Qt thread."""

from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from dotenv import load_dotenv

load_dotenv()

from src.main import search


class WorkerSignals(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)


class SearchWorker(QRunnable):
    """Runs the full search pipeline in a thread pool."""

    def __init__(self, query: str):
        super().__init__()
        self.query = query
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = search(self.query)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
