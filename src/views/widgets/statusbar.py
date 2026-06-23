"""Status bar widget for the main window."""

from PyQt6.QtWidgets import QLabel, QStatusBar, QWidget


class StatusBar(QStatusBar):
	"""Build the status bar and expose concise update helpers."""

	def __init__(self, parent: QWidget | None = None) -> None:
		super().__init__(parent)
		self.tool_status_label = QLabel("Tool: Select", self)
		self.cursor_status_label = QLabel("X: 0.00 m | Y: 0.00 m", self)
		self.snap_status_label = QLabel("Snap: -", self)
		self.length_status_label = QLabel("Length: -", self)
		self.area_status_label = QLabel("Area: 0.00 m2 | Living: 0.00 m2", self)

		self.addPermanentWidget(self.tool_status_label)
		self.addPermanentWidget(self.cursor_status_label)
		self.addPermanentWidget(self.snap_status_label)
		self.addPermanentWidget(self.length_status_label)
		self.addPermanentWidget(self.area_status_label)
		self.showMessage("Ready")

	def set_tool_text(self, text: str) -> None:
		"""Set active tool text in the status bar."""
		self.tool_status_label.setText(f"Tool: {text}")

	def set_cursor_position(self, x_mm: float, y_mm: float) -> None:
		"""Update cursor coordinates in meters."""
		self.cursor_status_label.setText(
			f"X: {x_mm / 1000.0:.2f} m | Y: {y_mm / 1000.0:.2f} m"
		)

	def set_preview_length(self, length_mm: float) -> None:
		"""Update live preview length indicator."""
		if length_mm < 0.0:
			self.length_status_label.setText("Length: -")
			return
		self.length_status_label.setText(f"Length: {length_mm / 1000.0:.2f} m")

	def set_snap_debug(self, enabled: bool, x_mm: float, y_mm: float) -> None:
		"""Update snap debug status indicator."""
		if not enabled:
			self.snap_status_label.setText("Snap: off")
			return
		self.snap_status_label.setText(
			f"Snap: ({x_mm / 1000.0:.2f}, {y_mm / 1000.0:.2f}) m"
		)
