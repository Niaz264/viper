with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

clone_end = """        if updater:
            updater.update(self.transferred_size, total_size)
        return Messages.COPIED_SUCCESSFULLY.format(file.get('name'), self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file.get('id')), humanbytes(total_size))
    except Exception as err:
      if isinstance(err, RetryError):
        LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
        err = err.last_attempt.exception()
      err_str = str(err).replace(">", "").replace("<", "")
      err_trace = traceback.format_exc()
      LOGGER.error(err_trace)
      return f"**ERROR:** ```{err_trace}```"

"""
content = content.replace("""        if updater:
            updater.update(self.transferred_size, total_size)
        return Messages.COPIED_SUCCESSFULLY.format(file.get('name'), self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file.get('id')), humanbytes(total_size))
""", clone_end)

with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
