import time

from centipede.ring_buffer import RingBuffer

TIMING_HISTORY = 15


class TimingManager(object):
    def __init__(self):
        self.incoming_jobs = RingBuffer(TIMING_HISTORY)
        self.limb_to_timings = {}


    def init_with_limbs(self, limbs):
        for limb in limbs:
            self.limb_to_timings[limb.__name__] = RingBuffer(TIMING_HISTORY)


    def record_incoming_job(self):
        self.incoming_jobs.add(time.time())


    def record_limb_input(self, limb):
        self.limb_to_timings[limb].add(time.time())


    def is_limb_slow(self, prev_limb, limb):
        limb_name = limb.__name__

        if not prev_limb:
            avg_prev_time = self.get_average_time_interval(self.incoming_jobs)
        else:
            prev_limb_name = prev_limb.__name__
            avg_prev_time = self.get_average_time_interval(self.limb_to_timings[prev_limb_name])

        avg_curr_time = self.get_average_time_interval(self.limb_to_timings[limb_name])

        if avg_prev_time and avg_curr_time:
            return avg_curr_time < avg_prev_time
        else:
            return False


    def get_average_time_interval(self, buffer):
        last_time = None
        time_intervals = []
        for time in buffer:
            if last_time:
                time_intervals.append(time - last_time)
                last_time = time

        avg = None
        if len(time_intervals):
            avg = sum(time_intervals) / len(time_intervals)

        return avg


    def reset_timing_info(self, limb):
        self.limb_to_timings[limb] = RingBuffer(TIMING_HISTORY)