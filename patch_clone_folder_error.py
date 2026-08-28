import re

with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

# Make cloneFolder also return traceback string
content = re.sub(
    r'except Exception as err:\n\s+LOGGER\.error\(traceback\.format_exc\(\)\)\n\s+return err',
    r'except Exception as err:\n                err_trace = traceback.format_exc()\n                LOGGER.error(err_trace)\n                return err_trace',
    content
)

with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
