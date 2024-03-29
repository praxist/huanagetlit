from __future__ import division

from datetime import datetime as dt
import bisect
import math
import random
import time

from bibliopixel.animation.matrix import Matrix
from clock import Clock
from clock import SubClock
import redis
import shared

import overlay
import shared

now = dt.now()
FREEFORALL = dt(now.year, now.month, now.day, 7, 50)

class MCP(Matrix):
    """Master control program."""

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.rc = shared.rc

        now = dt.now()

        self.t1 = False
        self.t1_hm = (6, 45)
        self.t1_duration = 150
        self.t1_dt = dt(now.year, now.month, now.day, self.t1_hm[0], self.t1_hm[1])

        self.t2 = False
        self.t2_hm = (7, 15)
        self.t2_duration = 150
        self.t2_dt = dt(now.year, now.month, now.day, self.t2_hm[0], self.t2_hm[1])

        self.t3 = False
        self.t3_hm = (7, 45)
        self.t3_duration = 150
        self.t3_dt = dt(now.year, now.month, now.day, self.t3_hm[0], self.t3_hm[1])

    def step(self, amt=1):
        now = dt.now()

        if self.t1:
            elapsed = int((now - self.t1_dt).total_seconds())
            if elapsed > self.t1_duration:
                self.rc.set("pattern_sparks", 0)
                self.rc.set("level_sparks", 0)
                self.t1 = False
            else:
                howmuch = int(elapsed / self.t1_duration * 255)
                self.rc.set("level_wave", howmuch)
                self.rc.set("level_sparks", 255 - howmuch)
        else:
            if (now.hour, now.minute) == self.t1_hm:
                self.rc.set("pattern_wave", 1)
                self.rc.set("level_wave", 0)
                self.t1 = True

        if self.t2:
            elapsed = int((now - self.t2_dt).total_seconds())
            if elapsed > self.t2_duration:
                self.rc.set("pattern_wave", 0)
                self.rc.set("level_wave", 0)
                self.t2 = False
            else:
                howmuch = int(elapsed / self.t2_duration * 255)
                self.rc.set("level_hydropump", howmuch)
                self.rc.set("level_wave", 255 - howmuch)
        else:
            if (now.hour, now.minute) == self.t2_hm:
                self.rc.set("pattern_hydropump", 1)
                self.rc.set("level_hydropump", 0)
                self.t2 = True

        if self.t3:
            elapsed = int((now - self.t3_dt).total_seconds())
            if elapsed > self.t3_duration:
                self.rc.set("pattern_hydropump", 0)
                self.rc.set("level_hydropump", 0)
                self.t3 = False
            else:
                howmuch = int(elapsed / self.t3_duration * 255)
                self.rc.set("level_embers", howmuch)
                self.rc.set("level_hydropump", 255 - howmuch)
        else:
            if (now.hour, now.minute) == self.t3_hm:
                self.rc.set("pattern_embers", 1)
                self.rc.set("level_embers", 0)
                self.t3 = True

        # change = (1, 15)

        # if (now.hour, now.minute) == change:
        #     if bool(int(self.rc.get("pattern_sparks"))):
        #         print("sparks no wave yes")
        #         self.rc.set("pattern_sparks", 0)
        #         self.rc.set("level_sparks", 0)
        #         self.rc.set("pattern_wave", 1)
        #         self.rc.set("level_wave", 255)
        #         print("DONE")


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

        self.rc = shared.rc
        self._last_fetch = 0
        self._morph = [[0 for x in range(self.layout.width)] for y in range(self.layout.height)]
        self._stickymorph = [[0 for x in range(self.layout.width)] for y in range(self.layout.height)]

        self.strobe = True
        self.on = False
        self.level = 255

    def fetch(self):
        ts, = map(int, self.rc.mget("ts"))
        # ts = int(self.rc.mget("ts"))

        # try:
        #     m = {k.decode(): v.decode() for k, v in self.rc.hgetall("morph").items()}
        #     for y in range(self.layout.height):
        #         self._morph[y] = [int(x) for x in  m[str(y)].split(',')]
        #     # print(self._morph)
        # except Exception as ex:
        #     print("Discarding morph data. Error: {}".format(ex))

        overlay.update_forces()
        self._morph = overlay.forces.vals
        # self._morph = list(zip(*overlay.forces.vals))

        self.on = bool(int(self.rc.get("pattern_wave") or 0))
        level = int(self.rc.get("level_wave") or 255)
        if not self.on:
            level = 0
        if self.level > level:
            self.level -= 10
            if self.level < level:
                self.level = level
        elif self.level < level:
            self.level += 10
            if self.level > level:
                self.level = level

        if ts > self._last_fetch:
            self._last_fetch = ts

    def step(self, amt=1):
        self.fetch()
        self.clock.update()

        self.strobe = not self.strobe

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
            return (1 + math.sin((w / self.layout.width + (2 * (1 -
                                                                self.slowclock.frac)))
                                 * num_waves * math.pi)) / 2

        pos_perc = 1.0
        # pos_perc = 1.0 - baseline_perc - wide_perc
        pos = [pos_perc * get_wave(x) for x in range(self.layout.width)]

        # Color spread per strip. At 0 each strip is a single color, at 255
        # each is a whole rainbow.
        window = 20

        # At 0 the strip colors are evenly distibuted in the rainbow, at 1 all
        # strips have the same starting/ending colors.
        squish = .8

        # Make color gradient chance in the opposite direction of wave
        # movement.
        revx = True

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
                hue = (int((255 * self.colorclock.frac) +
                           ((1 - squish) * 255 * y / self.layout.height) +
                           ((1 - x if revx else x)
                            * window / self.layout.width))
                       % 255)

                # default sat for non-strobing pixels
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
                    hue = (hue + 128) % 255
                    hi = int(255 / 100 * pressure)
                    sat = 255
                    # currently touching this spot (not fading out after touch)
                    if actual_pressure > 1:
                        # (other strobe options)
                        # sat = 80 + int((255 - 80) * abs(.5 - self.fastclock.frac))
                        # sat = int(255 * ((1 + math.sin(self.fastclock.frac * 2 * math.pi)) / 2))
                        if self.strobe:
                            # sat = 0
                            sat = 255 - int(255 / 100 * actual_pressure)

                hi = min(hi, self.level)
                self.layout.setHSV(x, y, (hue, sat, hi))


class Sparks(Matrix):
    def __init__(self, *args,
                 bpm=100,
                 multiple=1,
                 **kwds):
        super().__init__(*args, **kwds)
        self.clock = Clock(bpm, multiple)
        self.colorclock = self.clock.subclock(40, 1)

        self.rc = shared.rc
        self._last_fetch = 0
        self._last_frac = 0
        self.sattt = 0

        self.sparks = {}
        self.mtf = 0
        self.blooded = False

        # self.aftersparks = {}

        self.stepcount = 0

        self.faderate = 4
        self.steps_per_clock = 24  # sane default, blame this if pattern looks
                                   # bad at start

        # self.held = {i: 0 for i in range(self.layout.height + 1)}
        self.on = False
        self.level = 255

    def fetch(self):
        ts, = map(int, self.rc.mget("ts"))
        self.mtf = int(self.rc.get("morph_total_force"))
        self.on = bool(int(self.rc.get("pattern_sparks") or 0))
        self.level = int(self.rc.get("level_sparks") or 255)

        # TODO: only one pattern can update at a time
        now = time.time()
        overlay.update_buttons(self.rc.get("buttons"), now)
        overlay.update_sliders(self.rc.get("sliders"))

        self.sattt = int(2.5 * overlay.ls.percentage)
        self.faderate = 2 + int((20 - 2) * overlay.rs.percentage / 100)

        if ts > self._last_fetch:
            self._last_fetch = ts

    def step(self, amt=1):
        self.fetch()

        self.stepcount += 1
        self.clock.update()

        # if USE_TIME and self._last_frac > self.clock.frac:
        #     dt.now().hour

        # for i, (_, b) in enumerate(overlay.tbuttons.items()):
        #     if b.held: # and self.held[i] < 100:
        #         self.held[i] += 1
        #     else:
        #         self.held[i] = 0
        # print(self.held)

        # log-ish pressure gradient
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

        lmin = 80
        lmax = self.layout.height * self.layout.width

        wdex = [lmin + int((lmax - lmin) / len(levels) * i) for i in range(len(levels))]
        wdex.append(lmax)

        if self.on > 0:
            howmuch = self.mtf

            want = lmin
            if howmuch > levels[0]:
                want = wdex[bisect.bisect(levels, howmuch)]

            # limit the total number of sparks based on level instead of
            # brightness as in other patterns
            if self.level < 255:
                want = min(want, int(self.level * 255 / len(levels)))

            wantnow = math.ceil((want - len(self.sparks)) / self.steps_per_clock)
            if wantnow > 0:
                for x in range(wantnow):
                    k = (random.randint(0, self.layout.height),
                         random.randint(0, self.layout.width))
                    if k not in self.sparks:
                        self.sparks[k] = (255, self.faderate)

            if overlay.l1.pressed:
                for x in range(self.layout.width):
                    self.sparks[(0, x)] = (255, self.faderate)
                    # self.sparks[(0, x)] = (255, 2 + int(random.random() * 2 * self.faderate))
            if overlay.l2.pressed:
                for x in range(self.layout.width):
                    self.sparks[(1, x)] = (255, self.faderate)
                    # self.sparks[(1, x)] = (255, 2 + int(random.random() * 2 * self.faderate))
            if overlay.l3.pressed:
                for x in range(self.layout.width):
                    self.sparks[(2, x)] = (255, self.faderate)
                    # self.sparks[(2, x)] = (255, 2 + int(random.random() * 2 * self.faderate))
            if overlay.l4.pressed:
                for x in range(self.layout.width):
                    self.sparks[(3, x)] = (255, self.faderate)
                    # self.sparks[(3, x)] = (255, 2 + int(random.random() * 2 * self.faderate))
            if overlay.r4.pressed:
                for x in range(self.layout.width):
                    self.sparks[(4, x)] = (255, self.faderate)
                    # self.sparks[(4, x)] = (255, 2 + int(random.random() * 2 * self.faderate))
            if overlay.r3.pressed:
                for x in range(self.layout.width):
                    self.sparks[(5, x)] = (255, self.faderate)
                    # self.sparks[(5, x)] = (255, 2 + int(random.random() * 2 * self.faderate))
            if overlay.r2.pressed:
                for x in range(self.layout.width):
                    self.sparks[(6, x)] = (255, self.faderate)
                    # self.sparks[(6, x)] = (255, 2 + int(random.random() * 2 * self.faderate))
            if overlay.r1.pressed:
                for x in range(self.layout.width):
                    self.sparks[(7, x)] = (255, self.faderate)
                    # self.sparks[(7, x)] = (255, 2 + int(random.random() * 2 * self.faderate))

            # for i, (_, b) in enumerate(overlay.tbuttons.items()):
            #     if b.pressed:
            #         for x in range(self.layout.width):
            #             self.sparks[(i, x)] = (255, self.faderate)
            #             # if (i, x) not in self.sparks:
            #             #     self.sparks[(i, x)] = (255, self.faderate)
            #                 # self.sparks[(i, x)] = (255, int(random.random() * 2 * self.faderate))

        if self._last_frac > self.clock.frac:
            self.steps_per_clock = self.stepcount
            self.stepcount = 0

        # # choppy version, adds N sparks on clock rollover (version above smears)
        # if self._last_frac > self.clock.frac:
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
        #             self.sparks[k] = 255  # (TODO update for faderate)

        # Red warning flash
        startwarn = 80000
        maxwarn = 140000
        if self.mtf > startwarn:
            for y in range(self.layout.height):
                for x in range(self.layout.width):
                    self.layout.setHSV(x, y, (0, 220, int(100 * ((min(self.mtf,
                                                                      maxwarn)
                                                                  - startwarn)
                                                                 / (maxwarn -
                                                                    startwarn)))))
                    self.blooded = True
        if self.mtf <= 80000 and self.blooded:
            for y in range(self.layout.height):
                for x in range(self.layout.width):
                    self.layout.setHSV(x, y, (0, 0, 0))
                    self.blooded = False


        window = 50
        squish = .9
        revx = False

        # cribbed from Wave
        def gethue(y, x):
            if shared.interactive:
                return (int((255 * self.colorclock.frac) +
                            ((1 - squish) * 255 * y / self.layout.height) +
                            ((1 - x if revx else x)
                             * window / self.layout.width))
                        % 255)
            else:
                print("not interactive!")
                return ((x + 1) * (y + 1) * 37) % 256

        # for y, x in self.aftersparks.keys():
        #     ahue = gethue(y, x)
        #     _, abright, _ = self.aftersparks[(y, x)]
        #     self.layout.setHSV(x, y, (ahue, self.sattt, abright))

        for y, x in (self.sparks.keys()):
            hue = gethue(y, x)
            bright, faderate = self.sparks[(y, x)]

            # reverse fade
            # bright = 255 - bright

            # bright -= int(2.5 * self.held[y])
            # if bright < 0:
            #     bright = 0

            self.layout.setHSV(x, y, (hue, self.sattt, bright))

        af_soon = .9
        af_bright = .4

        delsparks = set()
        for k in self.sparks.keys():
            bright, faderate = self.sparks[k]
            self.sparks[k] = (bright - faderate, faderate)

            # # add aftersparks
            # if int(af_soon * 255) < bright < int(af_soon * 255) + faderate:
            #     n = int(af_bright * 255)
            #     y, x = k
            #     if x > 0:
            #         self.aftersparks[(y, x - 1)] = 'l', n, n
            #     if x < self.layout.width - 1:
            #         self.aftersparks[(y, x + 1)] = 'l', n, n

            if bright < faderate:
                delsparks.add(k)
        for k in delsparks:
            y, x = k
            self.layout.setHSV(x, y, (0, 0, 0))
            self.sparks.pop(k)

        # addafs = {}
        # delafs = set()
        # for k in self.aftersparks.keys():
        #     lr, abr, ast = self.aftersparks[k]
        #     abr -= faderate  # TODO: faderate
        #     self.aftersparks[k] = lr, abr, ast
        #     if max(0, int(ast - 3 * faderate)) < abr < int(ast - 2 * faderate) + faderate:
        #         print("got ast: {}".format(ast))
        #         y, x = k
        #         n = int(af_bright * ast)
        #         if x > 0 and lr == 'l':
        #             # print("OK - l")
        #             addafs[(y, x - 1)] = ('l', n, n)
        #         if x < self.layout.width - 1 and lr == 'r':
        #             # print("OK - r")
        #             addafs[(y, x + 1)] = ('r', n, n)
        #     elif abr < 20:
        #         delafs.add(k)
        # for k in addafs:
        #     self.aftersparks[k] = addafs[k]
        # for k in delafs:
        #     y, x = k
        #     if k not in self.sparks:
        #         self.layout.setHSV(x, y, (0, 0, 0))
        #     self.aftersparks.pop(k)

        self._last_frac = self.clock.frac


class EmberFireball:
    # def __init__(self, strip, size, start_frac, button, hue=None):
    def __init__(self, strip, size, start_frac, hue=None):
        self.strip = strip
        self.size = size
        self.start_frac = start_frac  # clock time at launch time
        # self.start_frac = -1  # doesnt launch until button released
        self.hue = hue
        self.frac = 0  # % down the strip, updated from update

        self._max_frac = start_frac
        self._min_frac = start_frac

        self._looped = False
        self._last_frac = start_frac
        self.ded = False
        # print(self.start_frac)

        self.last_head = 0  # total hack

        # self.button = button
        # self.launched = False
        # # how much size increments on every update call where button is held
        # self.power_increase_rate = 1

    # @property
    # def size(self):
    #     return int(self._size)

    def update(self, curr_frac):
        if not self._looped and (curr_frac < self._last_frac or curr_frac <
                                 self.start_frac):
            self._looped = True
        if curr_frac > self.start_frac and self._looped:
            self.ded = True

        if curr_frac == self.start_frac:
            self.frac = 0
        elif curr_frac > self.start_frac:
            self.frac = curr_frac - self.start_frac
        else:
            self.frac = 1 - self.start_frac + curr_frac
        if self.ded and self.frac > 0:
            self.frac += 1

        self._last_frac = curr_frac

class Embers(Matrix):
    """Comet with a trail of glowing embers."""
    def __init__(self, *args,
                 bpm=10,
                 multiple=1,
                 fade=0.9,
                 **kwds):

        super().__init__(*args, **kwds)
        # time to send a fireball down the strip
        self.clock = Clock(bpm, multiple)
        # (X, Y): launch Y/X times as fast as it takes to complete the strip
        self.launchclock = self.clock.subclock(3, 1)
        self.colorclock = self.clock.subclock(24, 1)
        self.fade = fade
        self.balls = []

        self.embers = {}

        self._last_frac = 0
        self.on = False
        self.level = 255

        self.frames_done = set()
        self.rdex = 0

        self.paused = False
        self.last_touch = 0
        self.pausetime = 10

    def fade_embers(self):
        ded = []

        # hi, lo = 1.3, .48

        for xy in self.embers:
            v, h, age = self.embers[xy]

            if age < 10:
                hi, lo = 1.30, .75
            elif 10 < age < 20:
                hi, lo = 1.25, .70
            elif 20 < age < 30:
                hi, lo = 1.20, .65
            elif 30 < age < 40:
                hi, lo = 1.15, .60
            else:
                hi, lo = 1.05, .55

            fade = lo + (hi - lo) * random.random()
            new_v = min(255, int(v * fade))
            if new_v == 0:
                ded.append(xy)
            self.embers[xy] = (new_v, h, age + 1)
        for xy in ded:
            del self.embers[xy]

    def fetch(self):
        now = time.time()
        # overlay.update_buttons(self.rc.get("buttons"), now)
        # overlay.update_sliders(self.rc.get("sliders"))
        self.on = bool(int(self.rc.get("pattern_embers") or 0))
        level = int(self.rc.get("level_embers") or 255)
        if self.level > level:
            self.level -= 10
            if self.level < level:
                self.level = level
        elif self.level < level:
            self.level += 10
            if self.level > level:
                self.level = level

    # TOTAL HACK that this is here, button presses aren't registering in MCP,
    # no idea why
    def only_sparks(self):
        self.rc.set("pattern_sparks", 1)
        self.rc.set("level_sparks", 255)
        self.rc.set("pattern_wave", 0)
        self.rc.set("level_wave", 0)
        self.rc.set("pattern_embers", 0)
        self.rc.set("level_embers", 0)
        self.rc.set("pattern_hydropump", 0)
        self.rc.set("level_hydropump", 0)

    def only_wave(self):
        self.rc.set("pattern_sparks", 0)
        self.rc.set("level_sparks", 0)
        self.rc.set("pattern_wave", 1)
        self.rc.set("level_wave", 255)
        self.rc.set("pattern_embers", 0)
        self.rc.set("level_embers", 0)
        self.rc.set("pattern_hydropump", 0)
        self.rc.set("level_hydropump", 0)

    def only_embers(self):
        self.rc.set("pattern_sparks", 0)
        self.rc.set("level_sparks", 0)
        self.rc.set("pattern_wave", 0)
        self.rc.set("level_wave", 0)
        self.rc.set("pattern_embers", 1)
        self.rc.set("level_embers", 255)
        self.rc.set("pattern_hydropump", 0)
        self.rc.set("level_hydropump", 0)

    def only_hydropump(self):
        self.rc.set("pattern_sparks", 0)
        self.rc.set("level_sparks", 0)
        self.rc.set("pattern_wave", 0)
        self.rc.set("level_wave", 0)
        self.rc.set("pattern_embers", 0)
        self.rc.set("level_embers", 0)
        self.rc.set("pattern_hydropump", 1)
        self.rc.set("level_hydropump", 255)

    def step(self, amt=1):
        self.fetch()

        self.clock.update()

        sparkprob = 100
        startbright = 128

        hi = 255
        lo = 20

        if overlay.t1.pressed and dt.now() > FREEFORALL:
            self.only_sparks()
        elif overlay.t2.pressed and dt.now() > FREEFORALL:
            self.only_wave()
        elif overlay.t3.pressed and dt.now() > FREEFORALL:
            self.only_hydropump()
        elif overlay.t7.pressed and dt.now() > FREEFORALL:
            self.only_embers()

        # animation script in the form:
        # - time in clock cycle to launch
        # - strips to launch
        # - hue
        reel = (
            (
                (.1, {0, 7}, 0),
                (.2, {1, 6}, 20),
                (.3, {2, 5}, 40),
                (.4, {3, 4}, 60),
                # (.5, set(), 0),
            ),
            (
                (.1, {3, 4}, 30),
                (.2, {2, 5}, 50),
                (.3, {1, 6}, 70),
                (.4, {0, 7}, 90),
                # (.5, set(), 0),
            ),
            (
                (.05, {0,}, 90),
                (.10, {1,}, 100),
                (.15, {2,}, 110),
                (.20, {3,}, 120),
                (.25, {4,}, 130),
                (.30, {5,}, 140),
                (.35, {6,}, 150),
                (.40, {7,}, 160),
                # (.5, set(), 0),
            ),
            (
                (.10, {7,}, 140),
                (.15, {6,}, 150),
                (.20, {5,}, 160),
                (.25, {4,}, 170),
                (.30, {3,}, 180),
                (.35, {2,}, 190),
                (.40, {1,}, 200),
                (.45, {0,}, 210),
                # (.5, set(), 0),
            ),
            (
                (0, {0, 1, 2, 3, 4, 5, 6, 7}, 220),
                (.2, {0, 1, 2, 3, 4, 5, 6, 7}, 50),
                (.4, {0, 1, 2, 3, 4, 5, 6, 7}, 220),
                (.6, {0, 1, 2, 3, 4, 5, 6, 7}, 50),
                (.8, {0, 1, 2, 3, 4, 5, 6, 7}, 220),
            ),
            (
                (0, {0, 1, 2, 3, 4, 5, 6, 7}, 250),
                (.2, {0, 1, 2, 3, 4, 5, 6, 7}, 80),
                (.4, {0, 1, 2, 3, 4, 5, 6, 7}, 250),
                (.6, {0, 1, 2, 3, 4, 5, 6, 7}, 80),
                (.8, {0, 1, 2, 3, 4, 5, 6, 7}, 250),
            ),
            # (
            #     (0, {0, 1, 2, 3, 4, 5, 6, 7}, 100),
            #     (.125, {0, 1, 2, 3, 4, 5, 6, 7}, 220),
            #     (.25, {0, 1, 2, 3, 4, 5, 6, 7}, 100),
            #     (.375, {0, 1, 2, 3, 4, 5, 6, 7}, 220),
            #     (.5, {0, 1, 2, 3, 4, 5, 6, 7}, 100),
            #     (.625, {0, 1, 2, 3, 4, 5, 6, 7}, 220),
            #     (.75, {0, 1, 2, 3, 4, 5, 6, 7}, 100),
            #     (.875, {0, 1, 2, 3, 4, 5, 6, 7}, 220),
            #     # (.9, set(), 0),
            # ),
        )

        reeltimes = [[t for t, v, h in r] for r in reel]


        if self.paused:
            if time.time() - self.last_touch > self.pausetime:
                self.paused = False

        if self.on > 0:

            if not self.paused:
                frame = bisect.bisect(reeltimes[self.rdex], self.launchclock.frac)
                if frame not in self.frames_done and frame < len(reel[self.rdex]):
                    for strip in reel[self.rdex][frame][1]:
                        self.balls.append(EmberFireball(
                            strip,
                            30,
                            self.clock.frac,
                            reel[self.rdex][frame][2]
                        ))
                    self.frames_done.add(frame)


            # Clock rolled over, switch to next animation in reel
            if self._last_frac > self.launchclock.frac:

                self.frames_done = set()
                self.rdex = (self.rdex + 1) % len(reel)

            # pushed a button, launch a fireball
            for i, b in enumerate(overlay.lrbuttons.values()):
                if b.pressed:
                    self.balls.append(EmberFireball(
                        i,
                        # random.randint(0, self.layout.height - 1),
                        44,
                        self.clock.frac,
                        random.randint(0, 255)
                    ))
                    self.paused = True
                    self.last_touch = time.time()


        vals = [[0 for x in range(self.layout.width)] for y in range(self.layout.height)]
        hues = [[0 for x in range(self.layout.width)] for y in range(self.layout.height)]

        dead_balls = []
        for i, fb in enumerate(self.balls):
            fb.update(self.clock.frac)
            width = self.layout.width
            v = [0] * width
            head = int(width * fb.frac)
            if head <= self.layout.width - 1:
                v[head] = 255
                if random.randint(0, 99) < sparkprob:
                    self.embers[(head, fb.strip)] = (startbright, fb.hue, 0)
                if head > fb.last_head:
                    for h in range(fb.last_head, head):
                        self.embers[(h, fb.strip)] = (startbright, fb.hue, 0)
                fb.last_head = head

            # tail should be gone at this point
            elif head - fb.size >= self.layout.width:
                dead_balls.append(i)
                continue

            for i in range(min(fb.size, head)):
                if head - i <= self.layout.width - 1:
                    v[head - i] = int(hi - (i * (hi - lo) / fb.size))

            # copy this ball's vals to the combined vals arr, set the hue for
            # all pixels with non-0 val to this ball's hue
            for i in range(len(v)):
                vals[fb.strip][i] = max(vals[fb.strip][i], v[i])
                if v[i] > 0:
                    hues[fb.strip][i] = fb.hue

        for i, b in enumerate(dead_balls):
            del self.balls[b - i]

        # draw fireball and embers
        for y in range(self.layout.height):
            for x in range(self.layout.width):
                ember_val, ember_hue, _ = self.embers.get((x, y), (0, 0, 0))
                if ember_val > 0:
                    self.layout.setHSV(x, y, (ember_hue, 255,
                                        min(max(vals[y][x], ember_val), self.level)))
                else:
                    self.layout.setHSV(x, y, (hues[y][x], 255, min(vals[y][x], self.level)))

        self.fade_embers()
        self._last_frac = self.launchclock.frac
