user_states = {}


def reset_state(user_id):
    user_states.pop(user_id, None)