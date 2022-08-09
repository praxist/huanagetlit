import math
import redis
import time

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
        pass
        # color = self.palette(self._step)
        # h = self.rc.hgetall("morph")
        # # print(h)

        # for i in range(self.layout.height):
        #     v = h[str(i)]
        #     a = v.split(",")

        #     # print("a ", len(a), a)

        #     for j in range(self.layout.width):
        #         val = int(a[j]) * 2

        #         # color = (255, 255, 255)
        #         color = [(255,0,0), (0,255,0), (0,0,255)][self._step % 3]
        #         if val > 0.75:
        #             self.layout.set(j, i, color)
        #         else:
        #             self.fade_pixel(j, i)

        # self._step += amt
