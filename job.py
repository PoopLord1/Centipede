import time

class Job(object):
	def __init__(self, data_point):
		self.init_time = time.time()
		self.data_point = data_point

	def 