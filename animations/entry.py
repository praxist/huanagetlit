import math
import redis
import time

from random import randrange

from clock import Clock
import overlay
import shared

from shared import fade_pixel

from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.colors import color_scale
from bibliopixel.colors.conversions import hsv2rgb_spectrum
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
        self.fade = 0.9
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

        if self._step % 2 == 0:
            overlay.update_forces()
            now = time.time()
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
            for j in range(self.layout.width):
                val = overlay.forces.get(j, i) * 2

                if val > 0:
                    self.layout.set(j, i, self.palette(val + self.shift))
                else:
                    self.fade_pixel(j, i)

        self._step += amt

class Confetti(Matrix):
    def __init__(self, *args,
                 fade=0.9,
                 max_confetti=10,
                 **kwds):

        # Fades previously lit pixels by a percentage
        self.fade = fade
        self.max_confetti = max_confetti
        super().__init__(*args, **kwds)

    def step(self, amt=1):
        for x in range(self.layout.width):
            for y in range(self.layout.height):
                        fade_pixel(self.fade, self.layout, x, y)

        for _ in range(self.max_confetti):
            x = randrange(self.layout.width)
            y = randrange(self.layout.height)
            self.layout.setHSV(x, y, (self._step * x, 80, 255))
        self._step += amt


# Internal structure for HydroPump
class Waterfall:
    def __init__(self, max_level, pressure, gravity, starting_level=0, reverse_brightness=False):
        self.active = False
        self.rising = False
        self.starting_level = starting_level
        self.level = starting_level
        self.max_level = max_level
        self._color = 0
        self.reverse_brightness = reverse_brightness
        self.pressure = pressure
        self.gravity = gravity

    @property
    def color(self):
        if self.reverse_brightness:
            brightness = 255 - int(self.level / self.max_level * 255)
        else:
            brightness = int(self.level / self.max_level * 255)
            if not self.rising:
                brightness = 255
        return color_scale(self._color, brightness)


    def activate(self, color, pressure=0, gravity=0):
        if pressure == 0:
            pressure = self.pressure
        if gravity == 0:
            gravity = self.gravity
        if self.active:
            if not self.rising:
                self._color = color
                self.level = self.starting_level
                self.pressure = pressure
                self.gravity = gravity
        else:
            self.active = True
            self.rising = True
            self._color = color
            self.level = self.starting_level
            self.pressure = pressure
            self.gravity = gravity

    def update(self):
        if self.rising:
            self.level += self.pressure
            if self.level >= self.max_level:
                self.rising = False
        else:
            if self.level > 1:
                self.level -= int(self.gravity)
            else:
                self.active = False


"""
Waterfalls that shoot from either end of the strip, terminating at the middle.
"""
class HydroPump(Matrix):
    def __init__(self, *args,
                 fade=0.75,
                 pressure=2,
                 gravity=2,
                 pipe_rate=15,
                 **kwds):

        # Fades previously lit pixels by a percentage
        self.fade = fade
        self.clock = Clock(100, 1)
        self._last_frac = 0

        self.pause = 2

        # how fast the water level rises
        self.pressure = pressure

        # how fast the water level drops
        self.gravity = gravity

        # number of pipes active
        self.pipe_rate = pipe_rate

        # one waterfall per strip starting from either end
        self.waterfalls_left = []
        self.waterfalls_right = []
        #The base class MUST be initialized by calling super like this
        super().__init__(*args, **kwds)

        for i in range(self.layout.height):
            self.waterfalls_left.append(Waterfall(self.layout.width/2, self.pressure, self.gravity, starting_level=0))
            self.waterfalls_right.append(Waterfall(self.layout.width/2, self.pressure, self.gravity, starting_level=0))

    def update_water_levels(self, waterfalls):
        # how long to stay at peak water level
        for w in waterfalls:
            w.update()

    def activate_waterfalls(self):
        for i in [-1, 1]:
            active_time = int(self.layout.width / 2 * (self.pressure + self.gravity) / self.pipe_rate)
            if self._step % active_time == 0:
                newly_active = int(self.layout.height / 2) + i * int((self._step / active_time) % (self.layout.height / 2)) + min(0, i)
                c = abs((self.layout.height / 2) - newly_active + min(0, i))
                self.waterfalls_left[newly_active].activate(hsv2rgb_spectrum((int(self._step * 0.5 + 40 * c), 190, 255)), self.pressure, self.gravity)
                self.waterfalls_right[newly_active].activate(hsv2rgb_spectrum((int(self._step * 0.5 + 40 * c), 190, 255)), self.pressure, self.gravity)

    def activate_waterfalls_interactive(self):
        saturation = overlay.ls.percentage + 160
        gravity = (overlay.rs.percentage / 100 * 8) + 1
        for y in range(self.layout.height):
            f = sum(overlay.forces.vals[y])
            pressure = int(max(overlay.forces.vals[y]) * 8 / 100)
            if f > 20:
                self.waterfalls_left[y].activate(hsv2rgb_spectrum((int(self._step * 0.2 + f + 40 * y), saturation, 255)), pressure=pressure, gravity=gravity)
                self.waterfalls_right[y].activate(hsv2rgb_spectrum((int(self._step * 0.2 + f + 40 * y), saturation, 255)), pressure=pressure, gravity=gravity)

    def step(self, amt=1):
        self.clock.update()
        overlay.update_forces()
        overlay.update_sliders(self.rc.get("sliders"))
        if shared.interactive():
            self.activate_waterfalls_interactive()
        else:
            self.activate_waterfalls()
        self.update_water_levels(self.waterfalls_left)
        self.update_water_levels(self.waterfalls_right)

        for y in range(self.layout.height):
            for x in range(self.layout.width):
                # outside to inside
                if self.waterfalls_left[y].active and x < self.waterfalls_left[y].level:
                    self.layout.set(x, y, self.waterfalls_left[y].color)
                elif self.waterfalls_right[y].active and x >= self.layout.width - self.waterfalls_right[y].level:
                    self.layout.set(x, y, self.waterfalls_right[y].color)
                else:
                    if self.fade < 1:
                        fade_pixel(self.fade, self.layout ,x, y)
                    else:
                        self.layout.set(x, y, (0,0,0))
                """
                # inside to outside
                if self.waterfalls_left[y].active and x < self.layout.width / 2 - self.waterfalls_left[y].level:
                    self.layout.set(x, y, self.waterfalls_left[y].color)
                elif self.waterfalls_right[y].active and x >= self.layout.width / 2 + self.waterfalls_right[y].level:
                    self.layout.set(x, y, self.waterfalls_right[y].color)
                """

        self._step += amt
