"""Background worker for running the search pipeline off the main Qt thread."""

from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from dotenv import load_dotenv

load_dotenv()

from src.main import search_with_progress


class WorkerSignals(QObject):
    progress = pyqtSignal(int, str)  # percent, label
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)


class SearchWorker(QRunnable):
    """Runs the full search pipeline in a thread pool, emitting progress."""

    def __init__(self, query: str):
        super().__init__()
        self.query = query
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            for step_name, label, percent, state in search_with_progress(self.query):
                if state is None:
                    self.signals.progress.emit(percent, label)
                else:
                    self.signals.progress.emit(100, "Done")
                    self.signals.finished.emit(state)
        except Exception as e:
            self.signals.error.emit(str(e))
