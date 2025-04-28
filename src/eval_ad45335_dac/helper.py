from state import state

def bind_widget_to_state(get_widget_value, set_widget_value, state_obj_getter, state_attr, signal):
    # Update state when widget changes
    def on_widget_change(*args):
        setattr(state_obj_getter(), state_attr, get_widget_value())        
        print(state.config)
    signal.connect(on_widget_change)

    # Update widget when state changes (if you have a state-changed signal)
    state.state_changed.connect(
        lambda: set_widget_value(getattr(state_obj_getter(), state_attr))
    )