from collections import OrderedDict
import shared
import time
import math

UP = 0
DOWN = 1

class Slider:
    def __init__(self, name):
        self.name = name
        self.percentage = 0


class Button:
    def __init__(self, name):
        self.name = name
        self.last_up = 0
        self.last_down = 0
        self.previous_update = time.time()
        self.last_update = time.time()
        self.pressed = False
        self.released = False
        self.held = False

    def update(self, last_up, last_down, now):
        self.previous_update = self.last_update
        self.last_update = now
        self.last_up = last_up
        self.last_down = last_down

        self.held = self.last_down > self.previous_update

        prev_pressed = self.pressed
        self.pressed = self.last_down > self.previous_update and self.last_down > self.last_up and self.last_up > self.previous_update - (self.last_update - self.previous_update) * 2 and not prev_pressed
        if self.pressed:
            print("pressed")
        prev_released = self.released
        self.released = self.last_up > self.previous_update and self.last_down > self.previous_update - (self.last_update - self.previous_update) * 2 and self.last_up > self.last_down and not prev_released
        if self.released:
            print("released")

l1 = Button("l1")
l2 = Button("l2")
l3 = Button("l3")
l4 = Button("l4")
t1 = Button("t1")
t2 = Button("t2")
t3 = Button("t3")
t4 = Button("t4")
t5 = Button("t5")
t6 = Button("t6")
t7 = Button("t7")
t8 = Button("t8")
t9 = Button("t9")
r1 = Button("r1")
r2 = Button("r2")
r3 = Button("r3")
r4 = Button("r4")
rs = Slider("rs")
ls = Slider("ls")
buttons = {
    "l1": l1,
    "l2": l2,
    "l3": l3,
    "l4": l4,
    "t1": t1,
    "t2": t2,
    "t3": t3,
    "t4": t4,
    "t5": t5,
    "t6": t6,
    "t7": t7,
    "t8": t8,
    "t9": t9,
    "r1": r1,
    "r2": r2,
    "r3": r3,
    "r4": r4,
}
tbuttons = {
    "t1": t1,
    "t2": t2,
    "t3": t3,
    "t4": t4,
    "t5": t5,
    "t6": t6,
    "t7": t7,
    "t8": t8,
    #"t9": t9,
}
sliders = {
    "rs": rs,
    "ls": ls,
}
lrbuttons = OrderedDict((
    ("l1", l1),
    ("l2", l2),
    ("l3", l3),
    ("l4", l4),
    ("r4", r4),
    ("r3", r3),
    ("r2", r2),
    ("r1", r1),
))

def update_sliders(dat):
    sliders_dat = dat.split(",")
    for slider_dat in sliders_dat:
        name, percent = slider_dat.split("-")
        percent = int(percent)
        sliders[name].percentage = percent


def update_buttons(dat, now):
    buttons_dat = dat.split(",")
    for button_dat in buttons_dat:
        name, ts_up, ts_down = button_dat.split("-")
        buttons[name].update(float(ts_up), float(ts_down), now)

# TODO: better way of hardcoding this
WIDTH = 100
HEIGHT = 8

class Forces:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.vals = []
        tmp = [0] * width
        for i in range(height):
            self.vals.append(tmp.copy())

    def get(self, x, y):
        return self.vals[y][x]

forces = Forces(WIDTH, HEIGHT)

def update_forces(width=WIDTH, height=HEIGHT):
    global forces
    h = shared.rc.hgetall("morph")
    for i in range(height):
        v = h[str(i)]
        a = v.split(",")
        for j in range(width):
            val = int(a[j])
            forces.vals[i][j] = val
