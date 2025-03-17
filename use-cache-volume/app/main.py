from time import sleep
import actfw_core
from actfw_core.task.task import Task
import subprocess
from datetime import datetime

FILE_PATH = "/mnt/cache_volume/cached_state.json"

class WritingFileTask(Task):
    def run(self):
        import os
        import json

        # ファイルが存在しない場合は初期データを作成
        if not os.path.exists(FILE_PATH):
            initial_data = {
                "count": 0,
                "datetime": datetime.now().isoformat()
            }
            os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
            with open(FILE_PATH, "w") as f:
                json.dump(initial_data, f)

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
