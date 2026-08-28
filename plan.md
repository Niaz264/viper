1. **Error log in clone command:** Modify the exception handling in `GoogleDrive.clone()` and `GoogleDrive.cloneFolder()` to return the full error stack trace (using `traceback.format_exc()`) when a cloning error occurs, so the user sees the complete error log.
2. **Progress Updater Utility:** Ensure `ProgressUpdater` in `bot/helpers/utils.py` correctly updates the Pyrogram message.
3. **Progress Bar for `clone` cmd:**
   - In `GoogleDrive.clone()`, first calculate the total size of the folder/file being cloned by recursing through it.
   - Pass the Pyrogram `message` and `total_size` to `cloneFolder()` or `copyFile()`.
   - Update the progress bar as each file is successfully copied.
4. **Progress Bar for `zip` and `unzip` cmd:**
   - Add a `message` parameter to `GoogleDrive.download()`, `download_file()`, and `downloadFolder()`. Update the progress bar iteratively while downloading.
   - Add a `message` parameter to `GoogleDrive.upload_file()`. Since it uses `MediaFileUpload` with `resumable=True`, we can use `request.next_chunk()` to get progress and update the message with ETA.
   - For `unzip` uploading extracted folder, we can calculate the total size of the extracted folder and keep a running total of uploaded bytes, passing this to `upload_file` or by managing the progress in the `upload_local_folder` loop.
5. **Pre-commit Instructions:** Run `pre_commit_instructions` before submitting to ensure testing, verifications, reviews and reflections are done.
6. **Submit:** Submit the changes.
