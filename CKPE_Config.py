import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QScrollArea, QTabWidget, QGridLayout, QLabel,
                              QCheckBox, QSpinBox, QLineEdit, QPushButton,
                              QFileDialog, QMessageBox, QComboBox, QStackedWidget, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class BrandingWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create heading
        heading = QLabel("Creation Kit Platform Extended")
        heading_font = QFont()
        heading_font.setPointSize(24)
        heading_font.setBold(True)
        heading.setFont(heading_font)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create subheading
        subheading = QLabel("INI Configuration Editor")
        subheading_font = QFont()
        subheading_font.setPointSize(16)
        subheading.setFont(subheading_font)
        subheading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create version
        version = QLabel("v1.0")
        version_font = QFont()
        version_font.setPointSize(12)
        version.setFont(version_font)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add some space between elements
        layout.addStretch()
        layout.addWidget(heading)
        layout.addSpacing(10)
        layout.addWidget(subheading)
        layout.addSpacing(5)
        layout.addWidget(version)
        layout.addStretch()

class ConfigEntry:
    def __init__(self, name, value, tooltip="", line_number=None):
        self.name = name
        self.value = value
        self.tooltip = tooltip
        self.line_number = line_number
        self.inline_comment = ""

class ConfigSection:
    def __init__(self, name, tooltip="", line_number=None):
        self.name = name
        self.tooltip = tooltip
        self.line_number = line_number
        self.entries = []

def parse_comments(lines, start_idx):
    """Extract comments above a section or entry."""
    comments = []
    idx = start_idx - 1
    while idx >= 0 and (lines[idx].strip().startswith(';') or not lines[idx].strip()):
        if lines[idx].strip().startswith(';'):
            comments.insert(0, lines[idx].strip()[1:].strip())
        idx -= 1
    return '\n'.join(comments)

def parse_ini_with_comments(file_path):
    """Parse INI file while preserving comments and line numbers."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sections = []
    current_section = None

    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith(';'):
            continue

        if line.startswith('[') and line.endswith(']'):
            section_name = line[1:-1]
            tooltip = parse_comments(lines, i)
            current_section = ConfigSection(section_name, tooltip, i)
            sections.append(current_section)
        elif '=' in line and current_section:
            name, value = line.split('=', 1)
            name = name.strip()
            value = value.strip()

            tooltip = parse_comments(lines, i)
            inline_comment = ""
            if ';' in value:
                value, inline_comment = value.split(';', 1)
                value = value.strip()
                if tooltip:
                    tooltip += '\n' + inline_comment.strip()
                else:
                    tooltip = inline_comment.strip()

            entry = ConfigEntry(name, value, tooltip, i)
            entry.inline_comment = inline_comment.strip()
            current_section.entries.append(entry)

    return sections, lines

class ConfigEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CreationKit Platform Extended INI Editor")
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)

        # Create stacked widget to switch between branding and editor
        self.stacked_widget = QStackedWidget()
        self.branding_widget = BrandingWidget()
        self.tab_widget = QTabWidget()

        self.stacked_widget.addWidget(self.branding_widget)
        self.stacked_widget.addWidget(self.tab_widget)

        main_layout.addWidget(self.stacked_widget)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        load_button = QPushButton("Load INI")
        save_button = QPushButton("Save INI")
        button_layout.addWidget(load_button)
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

        load_button.clicked.connect(self.load_ini)
        save_button.clicked.connect(self.save_ini)

        self.sections = []
        self.widgets = {}
        self.original_lines = []


    def create_widget_for_value(self, value, entry_name, section_name):
        """Create appropriate widget based on value type and section."""
        # Special case for Hotkeys and Log sections as well as the uTintMaskResolution entry in the Facegen section
        if section_name == "Hotkeys" or entry_name == "uTintMaskResolution" or section_name == "Log":
            widget = QLineEdit(value)
            return widget

        # Special case for nCharset - always use ComboBox
        if entry_name == "nCharset":
            widget = QComboBox()
            charsets = {
                "ANSI_CHARSET": 0,
                "DEFAULT_CHARSET": 1,
                "SYMBOL_CHARSET": 2,
                "SHIFTJIS_CHARSET": 128,
                "HANGEUL_CHARSET": 129,
                "GB2312_CHARSET": 134,
                "CHINESEBIG5_CHARSET": 136,
                "OEM_CHARSET": 255,
                "JOHAB_CHARSET": 130,
                "HEBREW_CHARSET": 177,
                "ARABIC_CHARSET": 178,
                "GREEK_CHARSET": 161,
                "TURKISH_CHARSET": 162,
                "VIETNAMESE_CHARSET": 163,
                "THAI_CHARSET": 222,
                "EASTEUROPE_CHARSET": 238,
                "RUSSIAN_CHARSET": 204,
                "MAC_CHARSET": 77,
                "BALTIC_CHARSET": 186
            }
            for charset_name, charset_value in charsets.items():
                widget.addItem(charset_name, charset_value)
            widget.setCurrentIndex(widget.findData(int(value)))
            return widget

        # Special case for uUIDarkThemeId - limit to values 0, 1, 2
        if entry_name == "uUIDarkThemeId":
            widget = QComboBox()
            themes = {
                "Lighter": 0,
                "Darker": 1,
                "Custom": 2
            }
            for theme_name, theme_value in themes.items():
                widget.addItem(theme_name, theme_value)
            widget.setCurrentIndex(widget.findData(int(value)))
            return widget

        # For other entries, use the normal logic
        if value.lower() in ('true', 'false'):
            widget = QCheckBox()
            widget.setChecked(value.lower() == 'true')
        elif value.isdigit():
            widget = QSpinBox()
            widget.setMaximum(999999)
            widget.setValue(int(value))
        else:
            widget = QLineEdit(value)
        return widget

    def create_section_widget(self, section):
        """Create a widget for a section with proper layout and alignment."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)  # Reduce spacing between entries
        layout.setContentsMargins(10, 10, 10, 10)  # Add some padding around the edges

        # Create a widget to hold the grid
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(5)  # Reduce spacing in the grid
        grid_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from grid

        # Add entries to grid
        for i, entry in enumerate(section.entries):
            # Label
            label = QLabel(entry.name)
            if entry.tooltip:
                label.setToolTip(entry.tooltip)
            grid_layout.addWidget(label, i, 0)

            # Value widget
            widget = self.create_widget_for_value(entry.value, entry.name, section.name)
            grid_layout.addWidget(widget, i, 1)

            self.widgets[(section.name, entry.name)] = widget

        # Add the grid to the layout
        layout.addWidget(grid_widget)

        # Add stretch at the bottom to push content to top
        layout.addStretch()

        return container

    def refresh_ui(self):
        """Refresh the UI with current sections and entries."""
        self.tab_widget.clear()
        self.widgets.clear()

        for section in self.sections:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            container = self.create_section_widget(section)
            scroll.setWidget(container)

            self.tab_widget.addTab(scroll, section.name)
            if section.tooltip:
                self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, section.tooltip)

        # Switch to the editor view now that we have content
        self.stacked_widget.setCurrentWidget(self.tab_widget)

    def verify_filename(self, filepath, operation="load"):
        """Verify that the file has the correct name."""
        expected_name = "CreationKitPlatformExtended.ini"
        actual_name = Path(filepath).name

        if actual_name != expected_name:
            QMessageBox.warning(
                self,
                "Invalid Filename",
                f"The {operation} filename must be '{expected_name}'\nSelected file: '{actual_name}'"
            )
            return False
        return True

    def load_ini(self):
        """Load and parse INI file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open INI file", "", "INI file (CreationKitPlatformExtended.ini)",)
        if not file_name:
            return

        if not self.verify_filename(file_name, "selected"):
            return

        self.sections, self.original_lines = parse_ini_with_comments(file_name)
        self.current_file = file_name
        self.refresh_ui()

    def save_ini(self):
        """Save current configuration while preserving comments and formatting."""
        if not hasattr(self, 'current_file'):
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save INI file", "CreationKitPlatformExtended.ini", "INI files (CreationKitPlatformExtended.ini)")
            if not file_name:
                return

            if not self.verify_filename(file_name, "save"):
                return

            self.current_file = file_name

        new_lines = self.original_lines.copy()

        for section in self.sections:
            for entry in section.entries:
                widget = self.widgets[(section.name, entry.name)]

                if isinstance(widget, QCheckBox):
                    value = str(widget.isChecked()).lower()
                elif isinstance(widget, QSpinBox):
                    value = str(widget.value())
                elif isinstance(widget, QComboBox):
                    value = str(widget.currentData())
                else:
                    value = widget.text()

                if hasattr(entry, 'inline_comment') and entry.inline_comment:
                    new_line = f"{entry.name}={value}\t\t\t; {entry.inline_comment}"
                else:
                    new_line = f"{entry.name}={value}"

                leading_space = len(new_lines[entry.line_number]) - len(new_lines[entry.line_number].lstrip())
                new_lines[entry.line_number] = ' ' * leading_space + new_line + '\n'

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            QMessageBox.information(self, "Success", "File saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = ConfigEditor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
