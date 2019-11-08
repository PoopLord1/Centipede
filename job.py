import time


class Job(object):
    def __init__(self, data_point, repeat):
        self.init_time = time.time()
        self.data_point = data_point
        self.period = 0
        self.scheduled_time = None
        self.repeat = repeat

    def set_period(self, period_seconds):
        self.period = period_seconds

    def schedule_job(self, datetime_obj):
        self.scheduled_time = datetime_obj

    def is_ready(self):
        now = time.time()
        if now > self.init_time + self.period:
            return True
        else:
            return False

    def repeat(self):
        new_job = Job(self.data_point)
        return new_job
