from time import sleep
import actfw_core
from actfw_core.task.task import Task
import subprocess
from datetime import datetime
import os
import json

FILE_PATH = "/mnt/cache_volume/cached_state.json"

class WritingFileTask(Task):
    def run(self):
        # /mnt/cache_volumeのファイル一覧を取得して通知
        result = subprocess.run(['ls', '-la', '/mnt/cache_volume'], capture_output=True, text=True)
        actfw_core.notify([{
            "message": f"ls -la /mnt/cache_volume\n{result.stdout}"
        }])

        # ファイルが存在しない場合は初期データを作成
        if not os.path.exists(FILE_PATH):
            initial_data = {
                "count": 0,
                "datetime": datetime.now().isoformat()
            }
            with open(FILE_PATH, "w") as f:
                json.dump(initial_data, f)
            actfw_core.notify([{
                "message": f"file created: {FILE_PATH}"
            }])

        # ファイルを読み込んでカウントアップ
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            last_count = data["count"]
            last_date = data["datetime"]
            # 現在の状態を通知
            actfw_core.notify([{
                "message": f"Count: {last_count}, last_date: {last_date}"
            }])
            data["count"] += 1
            data["datetime"] = datetime.now().isoformat()

        # 更新したデータを保存
        with open(FILE_PATH, "w") as f:
            json.dump(data, f)
            actfw_core.notify([{
                "message": f"file updated: {FILE_PATH}"
            }])

        while True:
            sleep(1)
            if not self._is_running():
                break


def main():
    # Actcast application
    app = actfw_core.Application()

    cmd = actfw_core.CommandServer()
    actfw_core.notify([{ "message": "start up" }])

    app.register_task(cmd)
    app.register_task(WritingFileTask())

    app.run()

if __name__ == "__main__":
    main()
