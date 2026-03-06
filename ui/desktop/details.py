"""Paper details screen."""

from __future__ import annotations

import subprocess
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QMouseEvent, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.storage import is_saved, save_article
from ui.desktop.theme import COLORS


class DetailsView(QWidget):
    """Full-screen detail view for a single paper."""

    def __init__(self, paper: dict, parent=None, on_save_change: Callable | None = None):
        super().__init__(parent)
        self.paper = paper
        self._on_save_change = on_save_change
        self._dirty = False
        self._build_ui()

        # Keyboard shortcuts
        for key in (Qt.Modifier.ALT | Qt.Key.Key_Left, Qt.Key.Key_Backspace):
            QShortcut(QKeySequence(key), self).activated.connect(self._go_back)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.BackButton:
            self._go_back()
        else:
            super().mouseReleaseEvent(event)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Top bar: back + save
        top_bar = QHBoxLayout()

        back_btn = QPushButton("< Back")
        back_btn.setObjectName("ghost")
        back_btn.setFixedHeight(36)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self._go_back)
        top_bar.addWidget(back_btn)

        top_bar.addStretch()

        self.save_btn = QPushButton()
        self.save_btn.setFixedHeight(36)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_save_btn()
        self.save_btn.clicked.connect(self._on_save)
        top_bar.addWidget(self.save_btn)

        layout.addLayout(top_bar)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(14)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel(self.paper.get("meta", {}).get("title", "Untitled"))
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {COLORS['text']};")
        content_layout.addWidget(title)

        # ID + Score — plain text, no background
        paper_id = self.paper.get("id", "N/A")
        score = self.paper.get("score", 0)
        meta_label = QLabel(f"arXiv: {paper_id}  |  Relevance: {score:.4f}")
        meta_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_dim']};")
        content_layout.addWidget(meta_label)

        # Divider
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {COLORS['border']};")
        content_layout.addWidget(divider)

        # Abstract
        abstract_header = QLabel("Abstract")
        abstract_header.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {COLORS['text_muted']};"
            "text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;"
        )
        content_layout.addWidget(abstract_header)

        abstract = QLabel(self.paper.get("text", "No abstract available."))
        abstract.setWordWrap(True)
        abstract.setStyleSheet(f"font-size: 14px; color: {COLORS['text']}; line-height: 1.6;")
        abstract.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_layout.addWidget(abstract)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Bottom bar with PDF button
        bottom = QHBoxLayout()
        bottom.addStretch()

        pdf_btn = QPushButton("Download PDF")
        pdf_btn.setObjectName("primary")
        pdf_btn.setFixedHeight(42)
        pdf_btn.setFixedWidth(180)
        pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pdf_btn.clicked.connect(self._download_pdf)
        bottom.addWidget(pdf_btn)

        layout.addLayout(bottom)

    def _update_save_btn(self):
        paper_id = self.paper.get("id", "")
        if is_saved(paper_id):
            self.save_btn.setText("Saved")
            self.save_btn.setObjectName("success")
            self.save_btn.setEnabled(False)
        else:
            self.save_btn.setText("Save Article")
            self.save_btn.setObjectName("primary")
            self.save_btn.setEnabled(True)
        self.save_btn.style().unpolish(self.save_btn)
        self.save_btn.style().polish(self.save_btn)

    def _on_save(self):
        save_article(self.paper)
        self._update_save_btn()
        self._dirty = True

    def _go_back(self):
        stack = self.parent()
        if stack:
            # Notify parent to refresh only after we're safely back
            if self._dirty and self._on_save_change:
                callback = self._on_save_change
            else:
                callback = None
            stack.setCurrentIndex(0)
            stack.removeWidget(self)
            self.deleteLater()
            if callback:
                callback()

    def _download_pdf(self):
        paper_id = self.paper.get("id", "")
        url = f"https://arxiv.org/pdf/{paper_id}"
        try:
            subprocess.Popen(["xdg-open", url])
        except Exception:
            pass
