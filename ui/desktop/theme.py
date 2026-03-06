"""Application-wide stylesheet and color palette."""

# Cohesive warm-gray palette — all surfaces on the same tonal ramp.
# Everything blends; accent is the only pop of color.
COLORS = {
    "bg": "#2b2d31",
    "surface": "#313338",
    "surface_hover": "#383a40",
    "border": "#3f4147",
    "border_hover": "#5865f2",
    "text": "#f2f3f5",
    "text_muted": "#b5bac1",
    "text_dim": "#80848e",
    "accent": "#5865f2",
    "accent_hover": "#4752c4",
    "accent_text": "#ffffff",
    "success": "#57f287",
    "success_dim": "#2d7d46",
    "danger": "#ed4245",
    "warning": "#fee75c",
}

STYLESHEET = f"""
QWidget {{
    background-color: {COLORS["bg"]};
    color: {COLORS["text"]};
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}}

QLineEdit {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
    color: {COLORS["text"]};
    selection-background-color: {COLORS["accent"]};
}}
QLineEdit:focus {{
    border-color: {COLORS["accent"]};
}}
QLineEdit::placeholder {{
    color: {COLORS["text_dim"]};
}}

QPushButton {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px 18px;
    color: {COLORS["text"]};
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {COLORS["surface_hover"]};
    border-color: {COLORS["border_hover"]};
}}
QPushButton:pressed {{
    background-color: {COLORS["border"]};
}}
QPushButton:disabled {{
    color: {COLORS["text_dim"]};
    border-color: {COLORS["border"]};
}}

QPushButton#primary {{
    background-color: {COLORS["accent"]};
    color: {COLORS["accent_text"]};
    border: none;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background-color: {COLORS["accent_hover"]};
}}
QPushButton#primary:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_dim"]};
}}

QPushButton#success {{
    background-color: {COLORS["success_dim"]};
    color: {COLORS["success"]};
    border: none;
    font-weight: 600;
}}
QPushButton#success:hover {{
    background-color: {COLORS["success_dim"]};
}}

QPushButton#danger {{
    background-color: transparent;
    color: {COLORS["danger"]};
    border: 1px solid {COLORS["border"]};
}}
QPushButton#danger:hover {{
    background-color: {COLORS["danger"]};
    color: {COLORS["accent_text"]};
    border-color: {COLORS["danger"]};
}}

QPushButton#ghost {{
    background-color: transparent;
    border: none;
    color: {COLORS["text_muted"]};
}}
QPushButton#ghost:hover {{
    color: {COLORS["text"]};
    background-color: {COLORS["surface_hover"]};
}}

QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    background-color: transparent;
    border: none;
    padding: 0px;
}}
QListWidget::item:selected {{
    background-color: transparent;
}}
QListWidget::item:hover {{
    background-color: transparent;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background-color: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 2px 0;
}}
QScrollBar::handle:vertical {{
    background-color: {COLORS["border"]};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["text_dim"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QTabWidget::pane {{
    border: none;
    background-color: {COLORS["bg"]};
}}
QTabBar::tab {{
    background-color: transparent;
    color: {COLORS["text_dim"]};
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 14px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {COLORS["text"]};
    border-bottom-color: {COLORS["accent"]};
}}
QTabBar::tab:hover:!selected {{
    color: {COLORS["text_muted"]};
    border-bottom-color: {COLORS["border"]};
}}

QTableWidget {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    gridline-color: {COLORS["border"]};
    selection-background-color: {COLORS["surface_hover"]};
}}
QTableWidget::item {{
    padding: 8px;
    border: none;
    color: {COLORS["text"]};
}}
QHeaderView::section {{
    background-color: {COLORS["surface"]};
    color: {COLORS["text_dim"]};
    border: none;
    border-bottom: 1px solid {COLORS["border"]};
    padding: 8px 12px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}}

QMessageBox {{
    background-color: {COLORS["surface"]};
}}
"""
