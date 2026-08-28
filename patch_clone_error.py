import re

with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

# Add traceback import if not present
if 'import traceback' not in content:
    content = content.replace('import json\n', 'import json\nimport traceback\n')

# Patch cloneFolder
content = re.sub(
    r'except Exception as err:\s+return err',
    r'except Exception as err:\n                LOGGER.error(traceback.format_exc())\n                return err',
    content
)

# Patch clone
content = re.sub(
    r'err = str\(err\)\.replace\(\'>\', \'\'\)\.replace\(\'<\', \'\'\)\n\s+LOGGER\.error\(err\)\n\s+return f"\*\*ERROR:\*\* ```\{err\}```"',
    r'err_str = str(err).replace(">", "").replace("<", "")\n      err_trace = traceback.format_exc()\n      LOGGER.error(err_trace)\n      return f"**ERROR:** ```{err_trace}```"',
    content
)

with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
