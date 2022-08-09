UP = 0
DOWN = 1

class Button:
    def __init__(self, name):
        self.name = name
        self.last_up = 0
        self.last_down = 0
        self.previous_update = 0
        self.last_update = 0

    def held(self):
        # check the button has been held down more recently than the last time
        # this was checked
        #print(self.last_update)
        #print(self.last_down)
        #print(self.previous_update)
        return self.last_down > self.previous_update

    def released(self):
        # check the button has been down before the last time this was checked
        # but self.last_update is up
        return self.last_up > self.previous_update and self.last_down > self.previous_update - (self.last_update - self.previous_update)

    def update(self, state, last_changed, now):
        self.previous_update = self.last_update
        self.last_update = now

        if state == UP:
           self.last_up = last_changed
        else:
           self.last_down = last_changed

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

def update_buttons(dat, now):
    buttons_dat = dat.split(",")
    for button_dat in buttons_dat:
        name, state, ts = button_dat.split("-")
        buttons[name].update(int(state), float(ts), now)
