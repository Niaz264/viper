import time
from bot.helpers.utils import ProgressUpdater

class MockMessage:
    def edit(self, text):
        print("MOCK EDIT CALLED WITH:")
        print(text)
        print("--------------------")

updater = ProgressUpdater(MockMessage(), "📤 **Uploading File...**\\n**Filename:** `test.zip`\\n**Size:** `1.5 MB`")
updater.update(500000, 1500000)
time.sleep(3.1)
updater.update(1000000, 1500000)
time.sleep(3.1)
updater.update(1500000, 1500000)
