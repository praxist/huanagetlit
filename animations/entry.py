import math
import redis
import time

import overlay

from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.animation.matrix import Matrix

class Entry(Matrix):
    """
    def __init__(self, *args,
                 **kwds):
        self.animations = [
            Something()
        ]

        super().__init__(*args, **kwds)

    def step(self, amt=1):
        self.animations[0].step()
        self.layout = self.animations[0].layout
    """
    def __init__(self, *args,
                 **kwds):
        self.fade = 0.97
        self.button_states = {}
        self.h = ""
        self.shift = 0

        super().__init__(*args, **kwds)

    # fades pixel at [i,j] by self.fade
    def fade_pixel(self, i, j):
        old = self.layout.get(i, j)
        if old != (0,0,0):
            self.layout.set(
                i, j,
                [math.floor(x * self.fade) for x in old]
            )

    def step(self, amt=1):
        color = self.palette(self._step)
        now = time.time()

        if self._step % 2 == 0:
            self.h = self.rc.hgetall("morph")
            overlay.update_buttons(self.rc.get("buttons"), now)
            overlay.update_sliders(self.rc.get("sliders"))
            self.shift = overlay.rs.percentage * 3

            if overlay.t1.pressed:
                self.shift += 20

            if overlay.t2.released:
                self.shift -= 20

        #self.set_palette("rainbow")

        for i in range(self.layout.height):
            v = self.h[str(i)]
            a = v.split(",")
            for j in range(self.layout.width):
                val = int(a[j]) * 2

                if val > 0:
                    self.layout.set(j, i, self.palette(val + self.shift))
                else:
                    self.fade_pixel(j, i)

        self._step += amt
