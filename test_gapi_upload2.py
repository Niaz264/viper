from googleapiclient.http import MediaFileUpload
from unittest.mock import MagicMock
import os
import io

# We need to figure out how `googleapiclient.http.MediaFileUpload` tracks progress.
print(dir(MediaFileUpload))
