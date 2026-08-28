import time
from unittest.mock import MagicMock

class MockMediaIoBaseDownload:
    def __init__(self):
        self.progress = 0
        self.total_size = 1000
    def next_chunk(self):
        self.progress += 200
        return MagicMock(resumable_progress=self.progress, total_size=self.total_size), self.progress >= self.total_size

d = MockMediaIoBaseDownload()
done = False
while not done:
    status, done = d.next_chunk()
    print(status.resumable_progress, status.total_size)
