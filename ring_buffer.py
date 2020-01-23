from collections import deque


class RingBuffer(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = deque([])
        self.i = 0

    def add(self, item):
        if len(self.buffer) == self.capacity:
            self.buffer.popleft()
        self.buffer.append(item)

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i < len(self.buffer):
            ret = self.buffer[self.i]
            self.i += 1
            return ret
        else:
            raise StopIteration