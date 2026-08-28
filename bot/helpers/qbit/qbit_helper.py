import os
import time
import qbittorrentapi
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.helpers.utils import CANCEL_TASKS, TaskCancelledError


class QbitHelper:
    def __init__(self):
        self.qbt_client = qbittorrentapi.Client(host='localhost:8080')
        try:
            self.qbt_client.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            LOGGER.error(f"qBittorrent login failed: {e}")

    def add_torrent(self, link):
        save_path = os.path.abspath(DOWNLOAD_DIRECTORY)
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        try:
            res = self.qbt_client.torrents_add(urls=link, save_path=save_path)
            if res != "Ok.":
                return False, f"Failed to add torrent: {res}"

            time.sleep(2)  # Wait a bit for the torrent to be added and parsed
            return True, "Torrent added"
        except Exception as e:
            return False, str(e)

    def get_latest_torrent(self, link):
        import urllib.parse as urlparse

        torrents = self.qbt_client.torrents_info()
        if not torrents:
            return None

        if link.startswith('magnet:'):
            try:
                params = urlparse.parse_qs(urlparse.urlparse(link).query)
                xt = params.get('xt', [''])[0]
                hash_id = xt.split(':')[-1].lower()
                for t in torrents:
                    if t.hash.lower() == hash_id:
                        return t
            except Exception:
                pass

        # Fallback to most recently added
        return sorted(torrents, key=lambda t: t.added_on, reverse=True)[0]

    def wait_for_download(self, link, updater, seed=False):
        try:
            torrent = None
            for _ in range(15):
                torrent = self.get_latest_torrent(link)
                if torrent:
                    break
                time.sleep(1)

            if not torrent:
                return False, "Failed to fetch torrent info from qBittorrent"

            hash_id = torrent.hash

            while True:
                if updater and updater.message and CANCEL_TASKS.get(updater.message.id):
                    self.qbt_client.torrents_delete(delete_files=True, torrent_hashes=hash_id)
                    raise TaskCancelledError("Task Cancelled")

                torrent_info = self.qbt_client.torrents_info(torrent_hashes=hash_id)[0]
                state = torrent_info.state

                if state in ["error", "missingFiles"]:
                    return False, "Torrent encountered an error"

                if state in ["downloading", "metaDL", "stalledDL", "checkingDL"]:
                    if updater:
                        updater.update(torrent_info.downloaded, torrent_info.total_size)

                if torrent_info.progress == 1.0 or state in ["uploading", "stalledUP", "queuedUP", "checkingUP", "pausedUP"]:
                    if updater:
                        updater.update(torrent_info.total_size, torrent_info.total_size)

                    file_path = os.path.join(torrent_info.save_path, torrent_info.name)

                    if not seed:
                        self.qbt_client.torrents_pause(torrent_hashes=hash_id)

                    return True, file_path

                time.sleep(2)
        except TaskCancelledError:
            return False, "Task Cancelled"
        except Exception as e:
            LOGGER.error(f"qBittorrent error: {e}")
            return False, str(e)

    def delete_torrent(self, hash_id, delete_files=False):
        try:
            self.qbt_client.torrents_delete(delete_files=delete_files, torrent_hashes=hash_id)
        except Exception as e:
            LOGGER.error(f"Failed to delete torrent: {e}")
