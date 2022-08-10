# Morph art overlay

import time

"""
Visualization of trackpad and buttons

t1 t2 t3 t4 t5 t6 t7 t8 t9
|  o  o  o  o  o  o  o   |
ls o  o  o  o  o  o  o  rs
l4 o  o  o  o  o  o  o  r4
l3 o  o  o  o  o  o  o  r3
l2 o  o  o  o  o  o  o  r2
l1 o  o  o  o  o  o  o  r1
--------------------------
"""

OVERLAY_TRACKPAD_TOP_LEFT = (12, 8)
OVERLAY_TRACKPAD_BOT_RIGHT = (172, 99)
MIN_BUT_FORCE = 50
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

MIN_SLI_FORCE = 40
SLIDERS = {
    # (x, (ymin, ymax))
    "ls": (4, (10, 41)),
    "rs": (179, (10, 41)),
}

UP = 0
DOWN = 1

button_states = {}
for b, _ in BUTTONS.items():
    # (up, down) timestamps
    button_states[b] = [0, 0]

slider_states = {}
for s, _ in SLIDERS.items():
    # 0-100 as a percentage of where the slider is active
    slider_states[s] = 0


def get_overlay_states(frame, info, debug):
    now = time.time()

    # check force coords of each button to determine state
    for name, coords in BUTTONS.items():
        x, y = coords
        if frame.force_array[y * info.num_cols + x] > MIN_BUT_FORCE:
            if debug:
                print(name)
            button_states[name][DOWN] = now
        else:
            button_states[name][UP] = now

    # check force coords of each slider to figure out at what point has maximum force
    for name, coords in SLIDERS.items():
        max_force = 0
        max_force_y = 0
        x, ys = coords
        ymin, ymax = ys

        for y in range(ymin, ymax):
            if frame.force_array[y * info.num_cols + x] > max_force:
                max_force = frame.force_array[y * info.num_cols + x]
                max_force_y = y

        # if force exceeds min, update slider data as a percentage of where the max force registered in the slider
        if max_force > MIN_SLI_FORCE:
            slider_length = ymax - ymin
            slider_states[name] = int((max_force_y - ymin) / slider_length * 100)

    # Write this to redis
    button_dat = ",".join(["%s-%s-%s" % (name, timestamps[UP], timestamps[DOWN]) for name, timestamps in
            button_states.items()])
    slider_dat = ",".join(["%s-%s" % (name, percent) for name, percent in slider_states.items()])

    if debug:
        print("Button data:\n%s" % button_dat)
        print("Slider data:\n%s" % slider_dat)

    return button_dat, slider_dat
