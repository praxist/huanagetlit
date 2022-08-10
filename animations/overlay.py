import time

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

    def held(self):
        # check the last time button was down was more recent than last frame
        return self.last_down > self.previous_update

    def released(self):
        # check the last time button was registered in both up and down states
        # since last frame
        if self.last_up > self.previous_update and self.last_down > self.previous_update - (self.last_update - self.previous_update) / 2 and self.last_up > self.last_down:
            print("released")
            return True

    def update(self, last_up, last_down, now):
        self.previous_update = self.last_update
        self.last_update = now
        self.last_up = last_up
        self.last_down = last_down

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
sliders = {
    "rs": rs,
    "ls": ls,
}

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
