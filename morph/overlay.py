# Morph art overlay

import time

"""
t1 t2 t3 t4 t5 t6 t7 t8 t9

ls                      rs
l4                      r4
l3                      r3
l2                      r2
l1                      r1
"""
OVERLAY_TRACKPAD_TOP_LEFT = (12, 8)
OVERLAY_TRACKPAD_BOT_RIGHT = (172, 99)
MIN_BUT_FORCE = 30
BUTTONS = {
    "l1": (5, 90),
    "l2": (5, 77),
    "l3": (5, 65),
    "l4": (4, 53),
    "t1": (16, 4),
    "t2": (35, 4),
    "t3": (49, 4),
    "t4": (76, 4),
    "t5": (92, 4),
    "t6": (105, 4),
    "t7": (135, 4),
    "t8": (148, 4),
    "t9": (165, 4),
    "r1": (179, 90),
    "r2": (179, 77),
    "r3": (179, 65),
    "r4": (179, 53),
}

UP = 0
DOWN = 1

button_states = {}
for b, _ in BUTTONS.items():
    # (up, down) timestamps
    button_states[b] = [0, 0]

def get_button_states(frame, info, debug):
    now = time.time()
    for name, coords in BUTTONS.items():
        x, y = coords
        if frame.force_array[y * info.num_cols + x] > MIN_BUT_FORCE:
            if debug:
                print(name)
            button_states[name][DOWN] = now
        else:
            button_states[name][UP] = now

    # Write this to redis
    dat = ""
    dat = ",".join(["%s-%s-%s" % (name, timestamps[UP], timestamps[DOWN]) for name, timestamps in
            button_states.items()])
    if debug:
        print(dat)
    return dat
