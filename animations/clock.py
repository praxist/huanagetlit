import shared
import time

def now_us():
    return int(time.time() * 1000000)

class Clock:
    """BPM clock to sync animations to music."""
    def __init__(self, bpm, multiple):
        self.set_bpm_attrs(bpm, multiple)
        self._reltime = self._last_zero_time = now_us()
        self._frac = 0
        self._last_fetch = 0
        self.rc = shared.rc
        self.subclocks = {}

    def fetch(self):
        """Set ts and bpm attrs from redis."""
        ts, bpm = map(int, self.rc.mget("ts", "bpm"))
        if ts > self._last_fetch:
            self.set_bpm_attrs(bpm, self.multiple)
            print("BPM IS {}".format(bpm))
            self._last_fetch = ts

    def set_bpm_attrs(self, bpm, multiple):
        """Update timing args, call to change bpm or multiple.

        The important var is _usbpm, or "microseconds per beat multiple". It's
        the interval in microseconds ("us") between beat-multiple events. E.g.
        at 100 BPM, multiple 4, there's 150000 us between events.
        """
        self._bpm = bpm
        self._multiple = multiple
        self._usbpm = 60000000 // (self._bpm * self._multiple)

    @property
    def bpm(self):
        return self._bpm

    @bpm.setter
    def bpm(self, val):
        self.set_bpm_attrs(val, self.multiple)

    @property
    def multiple(self):
        return self._multiple

    @multiple.setter
    def multiple(self, val):
        self.set_multiple_attrs(self.bpm, val)

    @property
    def usbpm(self):
        return self._usbpm

    @property
    def frac(self):
        return self._frac

    def update(self):
        """Updates internal timestamps, call from step.

        Call this before using frac in animations.

        This updates:
            _frac: how far we are into the current beat-multiple
            _reltime: the current time in us mod _usbpm, used to calculate
                      _frac
            _last_reltime: _reltime as of the last update
            _last_zero_time: _ the (interpolated) timestamp of the last
                             beat-multiple, we use it to calculate _reltime.
                             Note that we can't just use `now % _usbpm` because
                             we want to move smoothly between nearby bpms.
        """
        self.fetch()
        self._last_reltime = self._reltime
        now = now_us()
        self._reltime = (now - self._last_zero_time) % self._usbpm
        if self._reltime < self._last_reltime:
            self._last_zero_time = now - self._reltime
        self._frac = self._reltime / self._usbpm

        for sc in self.subclocks.values():
            sc._update(now)

    def subclock(self, num, denom):
        if (num, denom) in self.subclocks:
            return self.subclocks[(num, denom)]
        self.subclocks[(num, denom)] = SubClock(self, num, denom)
        return self.subclocks[(num, denom)]


class SubClock:
    """A clock synced to another clock."""
    def __init__(self, clock, num, denom):
        self.clock = clock
        self._num = num
        self._denom = denom

        self._reltime = self._last_zero_time = self.clock._last_zero_time
        self._frac = 0
        self._last_fetch = 0

    @property
    def usbpm(self):
        return int(self.clock.usbpm * self._num / self._denom)

    @property
    def frac(self):
        return self._frac

    def _update(self, now_us):
        # This is probably a stupid way to do this! Clocks probably drift apart
        # when we change the bpm. Use parent clock attrs and do some math
        # instead.
        usbpm = self.usbpm
        self._last_reltime = self._reltime
        self._reltime = (now_us - self._last_zero_time) % usbpm
        if self._reltime < self._last_reltime:
            self._last_zero_time = now_us - self._reltime
        self._frac = self._reltime / usbpm
