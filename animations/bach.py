from __future__ import division

import bisect
import math
import random

from bibliopixel.animation.matrix import Matrix
from strips import Clock
from strips import SubClock
import redis


class Id(Matrix):
    """ID strips"""

    def step(self, amt=1):
        for x in range(self.layout.width):
            self.layout.setRGB(x, 0, 255, 0, 0)
            self.layout.setRGB(x, 1, 0, 255, 0)
            self.layout.setRGB(x, 2, 0, 0, 255)
            self.layout.setRGB(x, 3, 200, 200, 200)
            if x % 2:
                self.layout.setRGB(x, 4, 255, 0, 0)
                self.layout.setRGB(x, 5, 0, 255, 0)
                self.layout.setRGB(x, 6, 0, 0, 255)
                self.layout.setRGB(x, 7, 200, 200, 200)

class Bump(Matrix):
    """Bump to the music"""
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.clock = Clock(100, 1)
        self.slowclock = self.clock.subclock(4, 1)
        self.fastclock = self.clock.subclock(1, 4)

    def step(self, amt=1):
        self.clock.update()

        def lit(clock):
            thold = 1 / 8
            if isinstance(clock, SubClock):
                thold = thold / (clock._num / clock._denom)
            if clock.frac < thold:
                return 255
            else:
                return 0
                # return int(128 * (1 - clock.frac))

        # r = 255 if self.slowclock.frac < 1/8 else self.slowclock.frac
        # g = 255 if self.clock.frac < 1/32 else 0
        # b = 255 if self.fastclock.frac < 1/128 else 0

        r = lit(self.slowclock)
        g = lit(self.clock)
        b = lit(self.fastclock)

        # r = int(255 * self.slowclock.frac)
        # g = int(255 * self.clock.frac)
        # b = int(255 * self.fastclock.frac)

        wsplit = int(self.layout.width / 3)
        for y in range(self.layout.height):
            # for x in range(self.layout.width):
            #     self.layout.set(x, y, (r, g, b))
            for x in range(wsplit):
                self.layout.set(x, y, (r, 0, 0))
            for x in range(wsplit, 2 * wsplit):
                self.layout.set(x, y, (0, g, 0))
            for x in range(2 * wsplit, self.layout.width):
                self.layout.set(x, y, (0, 0, b))


class Wave(Matrix):
    def __init__(self, *args,
                 bpm=100,
                 multiple=1,
                 **kwds):
        super().__init__(*args, **kwds)
        self.clock = Clock(bpm, multiple)

        self.fastclock = self.clock.subclock(1, 8)

        self.slowclock = self.clock.subclock(4, 1)
        self.slowclock2 = self.clock.subclock(4, 1)
        self.colorclock = self.clock.subclock(24, 1)

        self.rc = redis.Redis()
        self._last_fetch = 0
        self._morph = [[0 for x in range(self.layout.width)] for y in range(self.layout.height)]
        self._stickymorph = [[0 for x in range(self.layout.width)] for y in range(self.layout.height)]

        self.strobe = True
        self.threestep = 0

    def fetch(self):
        ts, = map(int, self.rc.mget("ts"))
        # ts = int(self.rc.mget("ts"))

        try:
            m = {k.decode(): v.decode() for k, v in self.rc.hgetall("morph").items()}
            for y in range(self.layout.height):
                self._morph[y] = [int(x) for x in  m[str(y)].split(',')]
            # print(self._morph)
        except Exception as ex:
            print("Discarding morph data. Error: {}".format(ex))

        if ts > self._last_fetch:
            self._last_fetch = ts

    def step(self, amt=1):
        self.clock.update()
        self.fetch()

        self.strobe = not self.strobe
        self.threestep = (self.threestep + 1) % 4

        for y in range(len(self._morph)):
            for x in range(len(self._morph[y])):
                val = self._morph[y][x]
                # # TODO: make this smooth? sig?
                if 0 < val and val <= 70:
                    val = 70
                # self._stickymorph[y][x] = (max(self._morph[y][x], self._stickymorph[y][x]))
                self._stickymorph[y][x] = (max(val, self._stickymorph[y][x]))
                self._stickymorph[y][x] -= 2

        # baseline_perc = .1
        # baseline_perc = .5
        baseline_perc = 0
        baseline = baseline_perc

        # everything up and down pulse
        wide_perc = 0
        # wide_perc = .5
        # wide_perc = 1
        wide = wide_perc * math.sin(math.pi * self.slowclock2.frac)

        # number of sine waves across the length of strips; the number of
        # visible troughs
        num_waves = 2

        def get_wave(w):
            x = (1 + math.sin((w / self.layout.width + (2 * (1 - self.slowclock.frac))) * num_waves * math.pi)) / 2
            # if x < 0:
            #     print("BAD", x)
            # if x > 1:
            #     print("BAD", x)
            return x
            # return (1 + math.sin((w / self.layout.width - self.clock.frac) * num_waves * math.pi)) / 2

        pos_perc = 1.0
        # pos_perc = 1.0 - baseline_perc - wide_perc
        pos = [pos_perc * get_wave(x) for x in range(self.layout.width)]
        # print(pos)

        for x in range(self.layout.width):
            thing = baseline + wide + pos[x]
            if thing > 1:
                print("bad", thing)

            hi = int(pos[x] * 255)
            # cnk: debug one pixel
            # if x == 50:
            #     print(hi)

            # hi = int((baseline + wide + pos[x]) * 255)

            for y in range(self.layout.height):

                # spread = 40
                # hue = y * (255 / (self.layout.height + 1))
                # hue += spread / self.layout.width * x
                # hue = int(y)

                # spread = 40
                # # hue = 40
                # hue = 40 * y
                # hue += (float(x) / self.layout.width) * spread
                # hue += 255 * self.slowclock.frac
                # hue = int(hue) % 255

                # Color spread per strip. At 0 each strip is a single color, at
                # 255 each is a whole rainbow.
                window = 20
                # window = 1

                # At 0 the strip colors are evenly distibuted in the rainbow,
                # at 1 all strips have the same starting/ending colors.
                squish = .8
                # squish = 0

                # Make color gradient chance in the opposite direction of wave
                # movement.
                revx = True
                hue = (int((255 * self.colorclock.frac) +
                           ((1 - squish) * 255 * y / self.layout.height) +
                           ((1 - x if revx else x)
                            * window / self.layout.width))
                       % 255)

                sat = 200

                # print((y, x))
                # print(type(self._morph[y][x]))
                # if self._stickymorph[y][x] > 10:
                #     print(y, x, self._morph[y][x])
                # print(len(self._morph))

                # scaled-up fading pressure, used for brightness
                pressure = self._stickymorph[y][x]
                # current actual pressure at the spot, used for strobe
                actual_pressure = self._morph[y][x]
                if pressure > 0:
                    # pressure = 100
                    # print("YES")
                    hue = (hue + 128) % 255
                    hi = int(255 / 100 * pressure)
                    # hi = 255
                    sat = 255
                    # currently touching this spot (not fading out after touch)
                    if actual_pressure > 1:

                        # sat = 40

                        # sat = 80 + int((255 - 80) * abs(.5 - self.fastclock.frac))
                        # # sat = int(255 * ((1 + math.sin(self.fastclock.frac * 2 * math.pi)) / 2))

                        # if self.threestep == 0:
                        #     sat = 255
                        # elif self.threestep == 1:
                        #     sat = 150
                        # elif self.threestep == 2:
                        #     sat = 40
                        # elif self.threestep == 3:
                        #     sat = 150

                        if self.strobe:
                            # sat = 0
                            sat = 255 - int(255 / 100 * actual_pressure)

                self.layout.setHSV(x, y, (hue, sat, hi))


class Sparks(Matrix):
    def __init__(self, *args,
                 bpm=100,
                 multiple=1,
                 **kwds):
        super().__init__(*args, **kwds)
        self.clock = Clock(bpm, multiple)
        self.fastclock = self.clock.subclock(1, 4)

        self.rc = redis.Redis()
        self._last_fetch = 0
        self._last_frac = 0

        # self.sparks = [[0 for x in range(self.layout.width)]
        #                for y in range(self.layout.height)]
        self.sparks = {}
        self.mtf = 0
        self.blooded = False

        self.steps_per_clock = 10  # blame this if pattern looks bad at start
        self.stepcount = 0

    def fetch(self):
        ts, = map(int, self.rc.mget("ts"))
        self.mtf = int(self.rc.get("morph_total_force"))
        # ts = int(self.rc.mget("ts"))

        if ts > self._last_fetch:
            self._last_fetch = ts

    def step(self, amt=1):
        self.stepcount += 1
        self.clock.update()
        self.fetch()

        levels = [100,
                  200,
                  400,
                  600,
                  800,
                  1200,
                  2000,
                  3000,
                  4000,
                  5000,
                  8000,
                  10000,
                  12000,
                  15000,
                  20000,
                  25000,
                  30000,
                  40000,
                  50000,
                  60000,
                  70000,
                  80000,
                  90000,
                  100000,
                  ]

        lmin = 40
        lmax = self.layout.height * self.layout.width

        wdex = [lmin + int((lmax - lmin) / len(levels) * i) for i in range(len(levels))]
        wdex.append(lmax)
        # print(wdex)

        # print(self.mtf)

        baseline_want = 10
        mul = 10

        # want = baseline_want - len(self.sparks)
        # want = max(lmin - len(self.sparks), 0)
        want = lmin
        if self.mtf > levels[0]:
            # want += (mul * bisect.bisect(levels, self.mtf))
            want = wdex[bisect.bisect(levels, self.mtf)]
        # want = math.ceil(want / self.steps_per_clock)
        wantnow = math.ceil((want - len(self.sparks))/ self.steps_per_clock)
        # print(self.mtf, want, len(self.sparks))
        if wantnow > 0:
            for x in range(wantnow):
                k = (random.randint(0, self.layout.height),
                     random.randint(0, self.layout.width))
                if k not in self.sparks:
                    self.sparks[k] = 255

        # # choppy version
        # # rolled over, add a spark
        # if self._last_frac > self.fastclock.frac:
        #     self.steps_per_clock = self.stepcount
        #     print("steps per clock", self.steps_per_clock)
        #     self.stepcount = 0

        #     spks = 1
        #     if self.mtf > levels[0]:
        #         for i, x in enumerate(levels):
        #             if self.mtf < x:
        #                 spks = 2 * i
        #                 print(i, self.mtf)
        #                 break

        #     for x in range(spks):
        #         k = (random.randint(0, self.layout.height),
        #              random.randint(0, self.layout.width))
        #         if k not in self.sparks:
        #             self.sparks[k] = 255

        # Red warning flash
        startwarn = 80000
        maxwarn = 140000
        if self.mtf > startwarn:
            for y in range(self.layout.height):
                for x in range(self.layout.width):
                    # thing = (min(self.mtf, 100000) - 50000) / 50000
                    # thing = int(255 * ((min(self.mtf, 100000) - 50000) / 50000))
                    # print(thing)
                    self.layout.setHSV(x, y, (0, 220, int(100 * ((min(self.mtf, maxwarn) - startwarn) / (maxwarn - startwarn)))))
                    self.blooded = True
        if self.mtf <= 80000 and self.blooded:
            for y in range(self.layout.height):
                for x in range(self.layout.width):
                    self.layout.setHSV(x, y, (0, 0, 0))
                    self.blooded = False

        for y, x in self.sparks.keys():
            self.layout.setHSV(x, y, (0, 0, self.sparks[(y, x)]))

        delme = set()
        for k in self.sparks.keys():
            self.sparks[k] = self.sparks[k] - 10
            if self.sparks[k] < 20:
                delme.add(k)
        for k in delme:
            y, x = k
            self.layout.setHSV(x, y, (0, 0, 0))
            self.sparks.pop(k)


        self._last_frac = self.fastclock.frac
