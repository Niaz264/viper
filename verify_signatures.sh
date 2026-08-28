echo "--- gDrive.py signatures ---"
grep -n "def clone(" bot/helpers/gdrive_utils/gDrive.py
grep -n "def cloneFolder(" bot/helpers/gdrive_utils/gDrive.py
grep -n "def copyFile(" bot/helpers/gdrive_utils/gDrive.py
grep -n "def download(" bot/helpers/gdrive_utils/gDrive.py
grep -n "def download_file(" bot/helpers/gdrive_utils/gDrive.py
grep -n "def downloadFolder(" bot/helpers/gdrive_utils/gDrive.py
grep -n "def upload_file(" bot/helpers/gdrive_utils/gDrive.py

echo "--- bot/plugins usages ---"
grep -rn "clone(" bot/plugins/
grep -rn "upload_file(" bot/plugins/
grep -rn "download(" bot/plugins/
