from state import state
from PySide6.QtWidgets import QLabel,  QComboBox

def bind_widget_to_state(get_widget_value, set_widget_value, state_obj_getter, state_attr, signal):
    # Update state when widget changes
    def on_widget_change(*args):
        setattr(state_obj_getter(), state_attr, get_widget_value())        
        print(state_obj_getter(), getattr(state_obj_getter(), state_attr))
    signal.connect(on_widget_change)

    # Update widget when state changes (if you have a state-changed signal)
    state.state_changed.connect(
        lambda: set_widget_value(getattr(state_obj_getter(), state_attr))
    )
    
def _add_channel_combo(options_grid, label, row, voltage_channels):
    options_grid.addWidget(QLabel(label), row, 0)
    combo = QComboBox()
    for vch in voltage_channels:
        display_text = f"channel {vch.port} on {vch.type}"
        combo.addItem(display_text, vch)
    options_grid.addWidget(combo, row, 1)
    return combo
