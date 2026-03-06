"""arXiv Agent Crawler — KDE/Qt native desktop UI."""

from __future__ import annotations

import subprocess
import sys

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.desktop.details import DetailsView
from src.storage import is_saved, load_saved, remove_article
from ui.desktop.theme import COLORS, STYLESHEET
from ui.desktop.worker import SearchWorker


# ---------------------------------------------------------------------------
# Paper card widget for the results list
# ---------------------------------------------------------------------------
class PaperCard(QFrame):
    """A single paper card in the results list."""

    def __init__(self, paper: dict, parent=None):
        super().__init__(parent)
        self.paper = paper
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("paperCard")
        self.setStyleSheet(
            f"""
            #paperCard {{
                background-color: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 10px;
                padding: 16px;
            }}
            #paperCard:hover {{
                border-color: {COLORS["accent"]};
                background-color: {COLORS["surface_hover"]};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 14, 16, 14)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel(paper.get("meta", {}).get("title", "Untitled"))
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLORS['text']};")
        title_row.addWidget(title, 1)

        # Saved indicator
        paper_id = paper.get("id", "")
        if is_saved(paper_id):
            saved_badge = QLabel("saved")
            saved_badge.setStyleSheet(
                f"color: {COLORS['success']}; font-size: 11px; font-weight: 600;"
            )
            saved_badge.setFixedHeight(20)
            title_row.addWidget(saved_badge, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(title_row)

        # Meta row
        score = paper.get("score", 0)
        meta = QLabel(f"arXiv: {paper_id}  |  Relevance: {score:.4f}")
        meta.setStyleSheet(f"font-size: 12px; color: {COLORS['text_muted']};")
        layout.addWidget(meta)

        # Abstract snippet
        abstract = paper.get("text", "")
        snippet = abstract[:180] + "..." if len(abstract) > 180 else abstract
        snippet_label = QLabel(snippet)
        snippet_label.setWordWrap(True)
        snippet_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_dim']}; margin-top: 4px;")
        layout.addWidget(snippet_label)


# ---------------------------------------------------------------------------
# Search tab
# ---------------------------------------------------------------------------
class SearchTab(QWidget):
    """Search input + results list."""

    def __init__(self, stack: QStackedWidget, on_saved_change=None):
        super().__init__()
        self.stack = stack
        self.on_saved_change = on_saved_change
        self.thread_pool = QThreadPool()
        self.papers: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Describe what you're researching...")
        self.search_input.setFixedHeight(44)
        self.search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("primary")
        self.search_btn.setFixedHeight(44)
        self.search_btn.setFixedWidth(110)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_btn)

        layout.addLayout(search_row)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_muted']};")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Results
        self.results_list = QListWidget()
        self.results_list.setSpacing(6)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.results_list, 1)

    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.search_btn.setEnabled(False)
        self.search_input.setEnabled(False)
        self.status_label.setText("Searching... this may take a moment")
        self.results_list.clear()
        self.papers.clear()

        worker = SearchWorker(query)
        worker.signals.finished.connect(self._on_results)
        worker.signals.error.connect(self._on_error)
        self.thread_pool.start(worker)

    def _on_results(self, result: dict):
        self.search_btn.setEnabled(True)
        self.search_input.setEnabled(True)
        ranked = result.get("ranked_results", [])
        quality = result.get("quality_score", 0)
        self.status_label.setText(f"{len(ranked)} results  |  Top relevance: {quality:.4f}")
        self.papers = ranked
        self._render_results()

    def _render_results(self):
        self.results_list.clear()
        for paper in self.papers:
            card = PaperCard(paper)
            item = QListWidgetItem()
            item.setSizeHint(card.sizeHint())
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, card)

    def _on_error(self, error: str):
        self.search_btn.setEnabled(True)
        self.search_input.setEnabled(True)
        self.status_label.setText("")
        QMessageBox.warning(self, "Search Error", error)

    def _on_item_clicked(self, item: QListWidgetItem):
        row = self.results_list.row(item)
        if 0 <= row < len(self.papers):
            details = DetailsView(
                self.papers[row],
                parent=self.stack,
                on_save_change=self._on_save_changed,
            )
            self.stack.addWidget(details)
            self.stack.setCurrentWidget(details)

    def _on_save_changed(self):
        self._render_results()
        if self.on_saved_change:
            self.on_saved_change()


# ---------------------------------------------------------------------------
# Saved articles tab
# ---------------------------------------------------------------------------
class SavedTab(QWidget):
    """Table of saved articles with actions."""

    def __init__(self, stack: QStackedWidget):
        super().__init__()
        self.stack = stack
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        self.empty_label = QLabel("No saved articles yet.\nSearch and save papers to build your reading list.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"font-size: 14px; color: {COLORS['text_dim']}; padding: 60px 0;")
        layout.addWidget(self.empty_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Title", "arXiv ID", "Score", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            self.table.styleSheet()
            + f"""
            QTableWidget::item:alternate {{
                background-color: {COLORS["surface_hover"]};
            }}
            """
        )
        layout.addWidget(self.table, 1)

    def refresh(self):
        articles = load_saved()
        has_articles = len(articles) > 0
        self.empty_label.setVisible(not has_articles)
        self.table.setVisible(has_articles)

        self.table.setRowCount(len(articles))
        for row, article in enumerate(reversed(articles)):
            # Title
            title_item = QTableWidgetItem(article.get("title", "Untitled"))
            self.table.setItem(row, 0, title_item)

            # ID
            paper_id = article.get("id", "N/A")
            id_item = QTableWidgetItem(paper_id)
            self.table.setItem(row, 1, id_item)

            # Score
            score = article.get("score", 0)
            score_item = QTableWidgetItem(f"{score:.4f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, score_item)

            # Actions
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(6)

            pdf_btn = QPushButton("PDF")
            pdf_btn.setObjectName("ghost")
            pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pdf_btn.setFixedHeight(28)
            pdf_btn.setStyleSheet(
                pdf_btn.styleSheet() + f"color: {COLORS['accent']}; font-size: 12px; font-weight: 600;"
            )
            pdf_btn.clicked.connect(lambda _, pid=paper_id: self._open_pdf(pid))
            actions_layout.addWidget(pdf_btn)

            remove_btn = QPushButton("Remove")
            remove_btn.setObjectName("danger")
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setFixedHeight(28)
            remove_btn.setStyleSheet(remove_btn.styleSheet() + "font-size: 12px;")
            remove_btn.clicked.connect(lambda _, pid=paper_id: self._remove(pid))
            actions_layout.addWidget(remove_btn)

            self.table.setCellWidget(row, 3, actions)
            self.table.setRowHeight(row, 48)

    def _open_pdf(self, paper_id: str):
        url = f"https://arxiv.org/pdf/{paper_id}"
        try:
            subprocess.Popen(["xdg-open", url])
        except Exception:
            pass

    def _remove(self, paper_id: str):
        remove_article(paper_id)
        self.refresh()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("arXiv Agent Crawler")
    app.setStyleSheet(STYLESHEET)

    window = QWidget()
    window.setWindowTitle("arXiv Agent Crawler")
    window.resize(900, 750)

    stack = QStackedWidget()

    # Main view with tabs
    main_view = QWidget()
    main_layout = QVBoxLayout(main_view)
    main_layout.setContentsMargins(28, 20, 28, 20)
    main_layout.setSpacing(0)

    # Header
    header = QLabel("arXiv Agent Search")
    header.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text']}; padding-bottom: 4px;")
    header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(header)

    subtitle = QLabel("AI-powered academic paper discovery")
    subtitle.setStyleSheet(f"font-size: 13px; color: {COLORS['text_dim']}; padding-bottom: 12px;")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(subtitle)

    # Tabs
    tabs = QTabWidget()
    saved_tab = SavedTab(stack)
    search_tab = SearchTab(stack, on_saved_change=saved_tab.refresh)
    tabs.addTab(search_tab, "Search")
    tabs.addTab(saved_tab, "Saved Articles")
    tabs.currentChanged.connect(lambda idx: saved_tab.refresh() if idx == 1 else None)
    main_layout.addWidget(tabs, 1)

    stack.addWidget(main_view)

    window_layout = QVBoxLayout(window)
    window_layout.setContentsMargins(0, 0, 0, 0)
    window_layout.addWidget(stack)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
