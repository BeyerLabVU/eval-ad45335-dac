from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget


class JoystickCircleWidget(QWidget):
    wheelScrolled = Signal(int)  # Signal to emit wheel delta changes

    xChanged = Signal(float) # Signals for saving the state
    yChanged = Signal(float)
    def __init__(self, outside_label):
        super().__init__()
        self.position_x = 0  # Current X position of the circle
        self.position_y = 0  # Current Y position of the circle
        
        self.locked = False
        self.wheel_sensitivity = 10
        self.label = outside_label
        self.dragging = False  # Track if dragging is happening

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the circle boundary
        center_x = self.width() // 2
        center_y = self.height() // 2
        self.radius = min(center_x, center_y) - 10

        painter.setPen(QPen(QColor("black"), 2))
        painter.setBrush(QColor("white"))
        painter.drawEllipse(center_x - self.radius, center_y - self.radius, self.radius * 2, self.radius * 2)

        # Map integral position to circle
        scaled_x = int(center_x + self.position_x)
        scaled_y = int(center_y - self.position_y)  # Invert Y-axis

        # Draw the moving circle
        painter.setBrush(QColor("red"))
        painter.drawEllipse(scaled_x - 5, scaled_y - 5, 10, 10)

    def set_position_x(self, x):
        self.position_x = x
        self.update()

    def set_position_y(self, y):
        self.position_y = y
        self.update()
        
    def update_position(self, dx, dy):
        if not self.locked:
            old_x = self.position_x
            old_y = self.position_y
            self.position_x += dx
            self.position_y += dy
            # Constrain the position to stay within the circle
            max_distance = self.radius
            distance = (self.position_x ** 2 + self.position_y ** 2) ** 0.5
            if distance > max_distance:
                scale = max_distance / distance
                self.position_x *= scale
                self.position_y *= scale
            self.update()
            self.label.setText(f"Deflection Setting: ({self.position_x / self.radius:.3f}, {self.position_y / self.radius:.3f})")
            if self.position_x != old_x:
                self.xChanged.emit(self.position_x)
            if self.position_y != old_y:
                            self.yChanged.emit(self.position_y)
                            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            center_x = self.width() // 2
            center_y = self.height() // 2
            click_x = event.position().x() - center_x
            click_y = center_y - event.position().y()  # Invert Y-axis

            # Check if the click is near the red circle
            distance = ((click_x - self.position_x) ** 2 + (click_y - self.position_y) ** 2) ** 0.5
            if distance <= 10:  # Circle radius for dragging
                self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging and not self.locked:
            center_x = self.width() // 2
            center_y = self.height() // 2
            new_x = event.position().x() - center_x
            new_y = center_y - event.position().y()  # Invert Y-axis

            self.update_position(new_x - self.position_x, new_y - self.position_y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ShiftModifier:
            # Move up or down
            self.update_position(0, 0.1 * self.wheel_sensitivity * (1 if event.angleDelta().y() > 0 else -1))
        elif event.modifiers() == Qt.ControlModifier:
            # Move left or right
            self.update_position(0.1 * self.wheel_sensitivity * (1 if event.angleDelta().y() > 0 else -1), 0)
        else:
            # Adjust sensitivity and emit signal for slider adjustment
            delta = 1 if event.angleDelta().y() > 0 else -1
            self.wheel_sensitivity += delta
            self.wheel_sensitivity = max(1, self.wheel_sensitivity)  # Ensure sensitivity stays positive
            self.wheelScrolled.emit(delta)  # Emit signal with wheel direction

    def lock_position(self):
        self.locked = True

    def unlock_position(self):
        self.locked = False