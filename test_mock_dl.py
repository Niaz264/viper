class MockStatus:
    def __init__(self, prog, total):
        self.resumable_progress = prog
        self.total_size = total
    def progress(self):
        return self.resumable_progress / self.total_size

s = MockStatus(500, 1000)
print(s.resumable_progress)
