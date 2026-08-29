import subprocess
import re
link = "https://proof.ovh.net/files/10Mb.dat"
process = subprocess.Popen(
    ["aria2c", "--console-log-level=warn", "--summary-interval=1", link],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)
for line in iter(process.stdout.readline, ""):
    print(repr(line))
process.wait()
