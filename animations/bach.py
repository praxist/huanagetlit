import math

from bibliopixel.animation.matrix import Matrix
from strips import Clock
from strips import SubClock
import redis


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
        self.slowclock = self.clock.subclock(16, 1)
        self.slowclock2 = self.clock.subclock(16, 1)

        self.rc = redis.Redis()
        self._last_fetch = 0

    def fetch(self):
        ts, = map(int, self.rc.mget("ts"))
        # ts = int(self.rc.mget("ts"))
        if ts > self._last_fetch:
            self._last_fetch = ts

    def step(self, amt=1):
        self.clock.update()
        self.fetch()

        baseline_perc = .1
        baseline = baseline_perc

        # everything up and down pulse
        wide_perc = .6
        wide = wide_perc * math.sin(math.pi * self.slowclock2.frac)

        num_waves = 2

        def get_wave(w):
            return math.sin((w / self.layout.width - self.clock.frac) * num_waves * math.pi)

        pos_perc = 1 - baseline_perc - wide_perc
        pos = [pos_perc * get_wave(x) for x in range(self.layout.width)]

        for x in range(self.layout.width):
            hi = int((baseline + wide + pos[x]) * 255)
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

                window = 40
                # window = 1

                # At 0 the strip colors are evenly distibuted in the rainbow,
                # at 1 all strips have the same starting/ending colors.

                squish = .5
                # squish = 0

                # Make color gradient chance in the opposite direction of wave
                # movement.
                revx = True
                hue = (int((255 * self.slowclock.frac) +
                           ((1 - squish) * 255 * y / self.layout.height) +
                           ((1 - x if revx else x)
                            * window / self.layout.width))
                       % 255)

                self.layout.setHSV(x, y, (hue, 255, hi))
