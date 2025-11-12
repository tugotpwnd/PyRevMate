from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QMessageBox
from views.left_menu_view import LeftMenuView
from views.operation_buttons_view import OperationButtonsView
from views.viewport_view import ViewportView
# --- ADD THESE IMPORTS ---
from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSettings
from .appearance_dialog import AppearanceDialog



class MainView(QMainWindow):
    # Define custom signals
    extract_signal = pyqtSignal()
    run_signal = pyqtSignal()

    def __init__(self, drawing_summary_manager):
        super().__init__()
        self.drawing_summary_manager = drawing_summary_manager
        self.setWindowTitle("PyRev Mate V_1.8")
        self.setGeometry(0, 0, 1920, 1080)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Left menu (Settings)
        self.left_menu = LeftMenuView(self.drawing_summary_manager)
        self.left_menu.setFixedWidth(self.width() // 4)  # Fixed to 1/4 of the window width
        main_layout.addWidget(self.left_menu)

        # Right layout for operations and viewport
        right_layout = QVBoxLayout()

        # Title and description
        title_label = QLabel("PyRev Mate V_1.8")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        right_layout.addWidget(title_label)

        description_label = QLabel("A tool to extract and manage AutoCAD attributes.")
        description_label.setWordWrap(True)
        right_layout.addWidget(description_label)

        # Operation buttons
        self.operation_buttons = OperationButtonsView()
        right_layout.addWidget(self.operation_buttons)

        # Connect OperationButtonsView signals to MainView signals
        self.operation_buttons.extract_signal.connect(self.extract_signal.emit)
        self.operation_buttons.run_signal.connect(self.run_signal.emit)

        # Add Viewport
        self.viewport = ViewportView()
        right_layout.addWidget(self.viewport)

        # Add right layout to main layout
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget)

        # --- ADD THIS MENU SETUP ---
        view_menu = self.menuBar().addMenu("View")
        act_appearance = QAction("Appearance…", self)
        act_appearance.triggered.connect(self._open_appearance_dialog)
        view_menu.addAction(act_appearance)

        # Ensure we have stable font baseline + apply saved theme now
        self._init_appearance_defaults()
        self._apply_theme()

    # === Appearance plumbing (Dark/Light + font delta) =========================
    def _qs(self) -> QSettings:
        # org/app names are arbitrary; change if you prefer
        return QSettings("Maxwell", "PyRevmate")

    def _init_appearance_defaults(self):
        app = QApplication.instance()
        default_font = app.font() if app else QFont()

        s = self._qs()
        if s.value("ui/base_point_size") is None:
            s.setValue("ui/base_point_size", default_font.pointSize() or 10)
        if s.value("ui/base_font_family") is None:
            s.setValue("ui/base_font_family", default_font.family() or QFont().family())
        if s.value("ui/theme") is None:
            s.setValue("ui/theme", "dark")
        if s.value("ui/font_delta") is None:
            s.setValue("ui/font_delta", 0)

        self._base_font_pt = int(s.value("ui/base_point_size", 10))
        self._base_font_family = str(s.value("ui/base_font_family", default_font.family()))

    def _open_appearance_dialog(self):
        s = self._qs()
        cur_theme = str(s.value("ui/theme", "dark")).lower()
        cur_delta = int(s.value("ui/font_delta", 0))
        dlg = AppearanceDialog(cur_theme, cur_delta, parent=self)
        if dlg.exec_() == dlg.Accepted:
            theme, delta = dlg.values()
            self._apply_appearance_values(theme, delta)

    def _apply_appearance_values(self, theme: str, delta: int):
        s = self._qs()
        s.setValue("ui/theme", theme)
        s.setValue("ui/font_delta", int(delta))
        self._apply_theme()

    def _apply_theme(self):
        s = self._qs()
        theme = str(s.value("ui/theme", "dark")).lower()
        font_delta = int(s.value("ui/font_delta", 0))

        # stable base (avoid compounding)
        target_pt = max(8, int(getattr(self, "_base_font_pt", 10)) + font_delta)
        app = QApplication.instance()
        if app:
            app.setFont(QFont(getattr(self, "_base_font_family", QFont().family()), target_pt))

        if theme == "light":
            accent = "#2D5BFF"
            panel = "#f7f8fb"
            border = "#d7deea"
            text = "#0b1325"
            subtext = "#5c6b82"
            pane_bg = "#ffffff"
            head_bg = "#eef2f8"
            list_bg = "#ffffff"
            sel_bg = "rgba(45,91,255,0.14)"
            tree_alt = "#f2f6fc"
            root_bg = "#ffffff"
            tab_txt = "#0b1325"
            tab_bg = "#e9eef7"
            tab_bg_hover = "#dfe7f4"
            tab_bg_sel = "#dfe7f4"
            btn_bg = "#f0f3f9"
            btn_bg_hover = "#e7ecf7"
            btn_bg_press = "#dfe7f4"
            sel_fg = "#000000"
        else:
            accent = "#4F7DFF"
            panel = "#0f1724"
            border = "#233044"
            text = "#E7ECF4"
            subtext = "#9fb3c8"
            pane_bg = "#0d1526"
            head_bg = "#121b2d"
            list_bg = "#0f1724"
            sel_bg = "rgba(79,125,255,0.35)"
            tree_alt = "#101a30"
            root_bg = "#0b1220"
            tab_txt = "rgba(255,255,255,0.92)"
            tab_bg = "#1b253a"
            tab_bg_hover = "#223154"
            tab_bg_sel = "#223154"
            btn_bg = "#19233a"
            btn_bg_hover = "#20304c"
            btn_bg_press = "#2b3e64"
            sel_fg = "#ffffff"

        tab_pt = target_pt + 2

        self.setStyleSheet(f"""
        /* Root + Dialogs */
        QMainWindow {{ background:{root_bg}; }}
        QDialog {{ background:{pane_bg}; color:{text}; }}
        QWidget {{ color:{text}; }}

        QLabel {{ color:{text}; }}

        /* Grouping */
        QGroupBox {{
            border:1px solid {border}; border-radius:12px; background:{pane_bg};
            margin-top:10px; padding-top:6px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin; left:10px; padding:0 6px; font-weight:700; color:{text};
        }}

        /* Menus */
        QMenuBar {{
            background:{panel}; color:{text}; border:0;
        }}
        QMenuBar::item {{
            background: transparent; padding:6px 10px; margin:0 4px; border-radius:8px;
        }}
        QMenuBar::item:selected {{ background:{tab_bg_hover}; color:{sel_fg}; }}
        QMenuBar::item:pressed  {{ background:{tab_bg_sel};  color:{sel_fg}; }}

        QMenu {{
            background:{panel}; color:{text}; border:1px solid {border}; border-radius:10px;
        }}
        QMenu::item {{ padding:6px 14px; border-radius:6px; }}
        QMenu::item:selected {{ background:{sel_bg}; color:{sel_fg}; }}

        /* Tables / Trees */
        QAbstractScrollArea {{ background: transparent; }}
        QTableWidget, QTreeWidget, QTreeView {{
            background: transparent; color:{text};
            alternate-background-color:{tree_alt};
            border:1px solid {border}; border-radius:10px;
        }}
        QHeaderView::section {{
            background:{head_bg}; color:{subtext};
            padding:7px 8px; border:0; border-right:1px solid {border}; font-weight:600;
        }}
        /* Selected rows/items for visibility */
        QAbstractItemView::item:selected {{
            background:{sel_bg}; color:{sel_fg};
        }}

        /* Inputs */
        QLineEdit, QComboBox, QTextEdit, QSpinBox {{
            background:{list_bg}; color:{text};
            border:1px solid {border}; border-radius:10px; padding:6px 9px;
            selection-background-color:{sel_bg}; selection-color:{sel_fg};
        }}
        QLineEdit::placeholder, QTextEdit::placeholder {{ color:{subtext}; }}

        /* Combo popup view */
        QComboBox QAbstractItemView {{
            background:{list_bg}; color:{text}; border:1px solid {border};
            selection-background-color:{sel_bg}; selection-color:{sel_fg};
        }}

        /* Buttons */
        QPushButton {{
            background:{btn_bg}; color:{text}; border:1px solid {border};
            border-radius:12px; padding:8px 12px; font-weight:600;
        }}
        QPushButton:hover  {{ background:{btn_bg_hover}; }}
        QPushButton:pressed{{ background:{btn_bg_press}; }}
        QPushButton#Primary {{ background:{accent}; color:white; border:none; }}

        /* Progress / Misc */
        QProgressBar {{
            border:1px solid {border}; border-radius:8px; text-align:center; background:{pane_bg};
        }}
        QProgressBar::chunk {{ background-color:{accent}; border-radius:8px; }}

        /* Tabs */
        QTabWidget::pane {{ background:{panel}; border:1px solid {border}; border-radius:12px; padding-top:6px; }}
        QTabBar::tab {{
            min-width: 160px; padding:8px 18px; margin:2px 6px;
            border-radius:12px; font-size:{tab_pt}pt; font-weight:800;
            color:{tab_txt}; background:{tab_bg};
        }}
        QTabBar::tab:hover    {{ background:{tab_bg_hover}; }}
        QTabBar::tab:selected {{ background:{tab_bg_sel}; color:{sel_fg}; }}

        QToolTip {{ background:{panel}; color:{text}; border:1px solid {border}; padding:6px; border-radius:6px; }}
        """)

        # Try to refresh map-fields row colors to adapt to theme immediately
        try:
            from views.viewport_view import ViewportView
            for vp in self.findChildren(ViewportView):
                vp.refresh_row_colors()
        except Exception:
            pass

        try:
            from views.mapping_dialog import MapFieldsDialog
            for dlg in self.findChildren(MapFieldsDialog):
                dlg.refresh_row_colors()
        except Exception:
            pass

    def show_error(self, message):
        """Display an error message."""
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec_()

    def get_settings(self):
        """Retrieve settings from the UI."""
        settings = {
            "purge": self.left_menu.purge_checkbox.isChecked(),
            "rename": self.left_menu.rename_checkbox.isChecked(),
            "plot": self.left_menu.plot_to_pdf_checkbox.isChecked(),
            "plot_style_table": self.left_menu.plot_style_text_box.text(),
            "transmit": self.left_menu.transmit_checkbox.isChecked(),
            "increment_revision": self.left_menu.increment_revision_checkbox.isChecked(),
            "revision_type": self.left_menu.dropdown.currentText(),
            "hardset_revision": self.left_menu.hardset_input.text() if self.left_menu.dropdown.currentText() == "Hardset Revision" else None,
            "attributes": {label: field.text() for label, field in self.left_menu.text_inputs.items()},
        }
        return settings
