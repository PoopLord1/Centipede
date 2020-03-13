import time

from centipede.internal.ring_buffer import RingBuffer

TIMING_HISTORY = 30
SAMPLES_NEEDED_FOR_TIMING = 5

class TimingManager(object):
    def __init__(self):
        self.incoming_jobs = RingBuffer(TIMING_HISTORY)
        self.limb_to_timings = {}
        self.process_to_timings = {}

        self.process_to_input_time = {}

    def init_with_limbs(self, limbs):
        for limb in limbs:
            self.limb_to_timings[limb.__name__] = RingBuffer(TIMING_HISTORY)


    def init_new_process(self, process_id):
        self.process_to_timings[process_id] = RingBuffer(TIMING_HISTORY)


    def record_incoming_job(self):
        self.incoming_jobs.add(time.time())


    def record_limb_input(self, limb):
        self.limb_to_timings[limb].add(time.time())


    def record_process_input(self, process_id):
        self.process_to_input_time[process_id] = time.time()


    def record_process_output(self, process_id):
        time_taken_for_job = time.time() - self.process_to_input_time[process_id]
        self.process_to_timings[process_id].add(time_taken_for_job)
        del self.process_to_input_time[process_id]


    def is_limb_slow(self, prev_limb, limb_name):
        avg_prev_time = None
        if not prev_limb:
            num_prev_samples = len(self.incoming_jobs)
            if num_prev_samples > SAMPLES_NEEDED_FOR_TIMING:
                avg_prev_time = self.get_average_time_interval(self.incoming_jobs)
        else:
            prev_limb_name = prev_limb
            num_prev_samples = len(self.limb_to_timings[prev_limb_name])
            if num_prev_samples > SAMPLES_NEEDED_FOR_TIMING:
                avg_prev_time = self.get_average_time_interval(self.limb_to_timings[prev_limb_name])

        avg_curr_time = None
        num_curr_samples = len(self.limb_to_timings[limb_name])
        if num_curr_samples > SAMPLES_NEEDED_FOR_TIMING:
            avg_curr_time = self.get_average_time_interval(self.limb_to_timings[limb_name])

        if avg_prev_time and avg_curr_time:
            return avg_curr_time > avg_prev_time
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


    def get_limb_processing_rate(self, limb_name=""):
        if not limb_name:
            return self.get_average_time_interval(self.incoming_jobs)
        return self.get_average_time_interval(self.limb_to_timings[limb_name])


    def get_process_processing_rate(self, process_id):
        if not process_id:
            raise Exception("You must provide a process id when getting a process' ingestion rate.")

        timings_sum = 0
        for time in self.process_to_timings[process_id]:
            timings_sum += time

        avg = None
        if len(self.process_to_timings[process_id]):
            avg = timings_sum / len(self.process_to_timings[process_id])

        return avg


    def reset_timing_info(self, limb):
        self.limb_to_timings[limb.__name__] = RingBuffer(TIMING_HISTORY)
