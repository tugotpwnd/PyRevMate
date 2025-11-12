# mapping_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QComboBox,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QColor, QDrag, QPalette, QBrush


# Robust imports (works whether you use a package structure or flat files)
try:
    from utils.helpers import load_mapping_from_json, save_mapping_to_json, resource_path
except Exception:
    from helpers import load_mapping_from_json, save_mapping_to_json, resource_path

def _is_dark(widget) -> bool:
    base = widget.palette().color(QPalette.Base)
    return base.value() < 128

def _contrast_fg(bg: QColor) -> QColor:
    if bg.alpha() == 0:
        return QColor()  # invalid -> inherit
    # simple luminance check
    lum = 0.2126*bg.red() + 0.7152*bg.green() + 0.0722*bg.blue()
    return QColor(0, 0, 0) if lum > 150 else QColor(255, 255, 255)



class AssignListWidget(QListWidget):
    """
    Left-hand list of allowable assignments.
    Overridden to drag out the item's text as text/plain so the combo boxes can accept it.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDefaultDropAction(Qt.CopyAction)

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if not item:
            return
        mime = QMimeData()
        mime.setText(item.text())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(Qt.CopyAction)


class DroppableComboBox(QComboBox):
    """A QComboBox that accepts drops of assignment names (text/plain)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setInsertPolicy(QComboBox.NoInsert)

    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        txt = e.mimeData().text().strip()
        idx = self.findText(txt)
        if idx >= 0:
            self.setCurrentIndex(idx)
        e.acceptProposedAction()


class MapFieldsDialog(QDialog):
    """
    Dialog to map extracted tags to assignment keys and persist them to JSON5.
    Rows: red (unmapped) / amber (changed) / green (matches existing).
    """
    def __init__(self, extracted_fields, assignment_options, mapping_filepath=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map Fields")
        self.setMinimumSize(840, 560)

        self.assignment_options = list(assignment_options or [])
        self.mapping_filepath = mapping_filepath or resource_path("Dict/AttributeDictionary.json5")

        try:
            self.existing_mapping = load_mapping_from_json(self.mapping_filepath)
        except Exception:
            self.existing_mapping = {}

        # Build tag -> sample value
        tag_samples = {}
        for item in extracted_fields or []:
            tag = (item.get("Tag") or "").strip()
            if tag and tag not in tag_samples:
                tag_samples[tag] = item.get("Value", "")

        # ---- Layouts ----
        root = QHBoxLayout(self)

        # Left: draggable list
        left = QVBoxLayout()
        title_l = QLabel("Assignable Keys (drag to a row's ‘Mapped Assignment’):")
        left.addWidget(title_l)

        self.assign_list = AssignListWidget()
        for opt in self.assignment_options:
            QListWidgetItem(opt, self.assign_list)
        # Nice: double-click an assignment to apply to all selected rows
        self.assign_list.itemDoubleClicked.connect(self._apply_to_selected_rows)
        left.addWidget(self.assign_list)
        root.addLayout(left, 1)

        # Right: table of tags
        right = QVBoxLayout()
        right.addWidget(QLabel("Extracted Fields"))

        self.table = QTableWidget(len(tag_samples), 4)
        self.table.setHorizontalHeaderLabels(["Tag", "Sample", "Mapped Assignment", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)

        for row, (tag, sample) in enumerate(sorted(tag_samples.items(), key=lambda x: x[0].lower())):
            self.table.setItem(row, 0, QTableWidgetItem(tag))
            self.table.setItem(row, 1, QTableWidgetItem(sample))

            combo = DroppableComboBox()
            combo.addItems(self.assignment_options)

            if tag in self.existing_mapping:
                want = self.existing_mapping[tag]
                idx = combo.findText(want)
                combo.setCurrentIndex(idx if idx >= 0 else -1)
            else:
                combo.setCurrentIndex(-1)

            combo.currentTextChanged.connect(lambda _t, r=row: self._update_row_status(r))
            self.table.setCellWidget(row, 2, combo)

            self.table.setItem(row, 3, QTableWidgetItem(""))  # status cell
            self._update_row_status(row)

        right.addWidget(self.table)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._handle_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        right.addLayout(btns)

        root.addLayout(right, 3)
        self.setLayout(root)

        # Small usage hint
        title_l.setToolTip("Drag an assignment from the left into the ‘Mapped Assignment’ cell.\n"
                           "Or, double-click an assignment to apply to all selected rows.")

    # ---------- Helpers ----------
    def _apply_to_selected_rows(self, item):
        txt = item.text().strip()
        for idx in self.table.selectionModel().selectedRows():
            row = idx.row()
            combo = self.table.cellWidget(row, 2)
            if combo:
                j = combo.findText(txt)
                if j >= 0:
                    combo.setCurrentIndex(j)
                self._update_row_status(row)

    def _set_row_color(self, row, bg: QColor):
        fg = _contrast_fg(bg)
        for c in range(self.table.columnCount()):
            it = self.table.item(row, c)
            if it is None:
                it = QTableWidgetItem("")
                self.table.setItem(row, c, it)
            # transparent -> clear brush so it inherits table bg
            it.setBackground(QBrush() if bg.alpha() == 0 else bg)
            it.setForeground(QBrush() if not fg.isValid() else QBrush(fg))

    def _update_row_status(self, row):
        combo = self.table.cellWidget(row, 2)
        tag = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
        mapped = combo.currentText().strip() if combo and combo.currentIndex() >= 0 else ""
        status_item = self.table.item(row, 3)

        dark = _is_dark(self.table)

        if not mapped:
            status_item.setText("Unmapped")
            bg = QColor(180, 70, 70, 170) if dark else QColor(255, 200, 200)  # red
            self._set_row_color(row, bg)
            return

        existing = self.existing_mapping.get(tag, "")
        if existing and existing == mapped:
            status_item.setText("Mapped (OK)")
            bg = QColor(60, 140, 95, 150) if dark else QColor(200, 255, 200)  # green
        else:
            status_item.setText("New/Changed")
            bg = QColor(180, 140, 60, 160) if dark else QColor(255, 240, 200)  # amber

        self._set_row_color(row, bg)

    def _collect_new_mappings(self):
        out = {}
        for row in range(self.table.rowCount()):
            tag = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            combo = self.table.cellWidget(row, 2)
            val = combo.currentText().strip() if combo and combo.currentIndex() >= 0 else ""
            if tag and val:
                out[tag] = val
        return out

    def _handle_save(self):
        new_map = self._collect_new_mappings()
        if not new_map:
            QMessageBox.warning(self, "Nothing to save", "No mappings were provided.")
            return

        merged = dict(self.existing_mapping)
        replace_all = None
        keep_all = None

        for tag, new_val in new_map.items():
            if tag not in merged:
                merged[tag] = new_val
                continue
            old_val = merged[tag]
            if old_val == new_val:
                continue

            # Conflict dialog
            box = QMessageBox(self)
            box.setWindowTitle("Mapping conflict")
            box.setIcon(QMessageBox.Question)
            box.setText(
                f"Tag '{tag}' exists.\nExisting: {old_val}\nNew: {new_val}\nReplace existing mapping?"
            )
            replace_btn = box.addButton("Replace", QMessageBox.AcceptRole)
            keep_btn = box.addButton("Keep existing", QMessageBox.RejectRole)
            replace_all_btn = box.addButton("Replace All", QMessageBox.YesRole)
            keep_all_btn = box.addButton("Keep All", QMessageBox.NoRole)
            cancel_btn = box.addButton("Cancel", QMessageBox.DestructiveRole)
            box.exec_()

            clicked = box.clickedButton()
            if clicked == cancel_btn:
                return
            elif clicked == replace_btn:
                merged[tag] = new_val
            elif clicked == keep_btn:
                pass
            elif clicked == replace_all_btn:
                replace_all = True
                merged[tag] = new_val
            elif clicked == keep_all_btn:
                keep_all = True
                pass

        try:
            save_mapping_to_json(self.mapping_filepath, merged)
            QMessageBox.information(self, "Saved", "Attribute dictionary updated.")
            self.accept()  # Main controller should handle reload + recolor
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def refresh_row_colors(self):
        for r in range(self.table.rowCount()):
            self._update_row_status(r)

