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
        def run_command(cmd, description):
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                error_msg = (
                    result.stderr
                    if result.stderr
                    else f"Command failed with exit code {result.returncode}"
                )
                actfw_core.notify([{"message": f"Error in {description}: {error_msg}"}])
                raise RuntimeError(
                    f"Command failed with exit code {result.returncode}: {error_msg}"
                )
            return result

        result = run_command(["ls", "-la", "/mnt"], "listing /mnt")
        actfw_core.notify([{"message": f"ls -la /mnt\n{result.stdout}"}])

        # /mnt/cache_volumeのファイル一覧を取得して通知
        result = run_command(
            ["ls", "-la", "/mnt/cache_volume"], "listing /mnt/cache_volume"
        )
        actfw_core.notify([{"message": f"ls -la /mnt/cache_volume\n{result.stdout}"}])

        actfw_core.notify([{"message": "check file exists"}])

        # ファイルが存在しない場合は初期データを作成
        if not os.path.exists(FILE_PATH):
            initial_data = {"count": 0, "datetime": datetime.now().isoformat()}
            with open(FILE_PATH, "w") as f:
                json.dump(initial_data, f)
            actfw_core.notify([{"message": f"file created: {FILE_PATH}"}])

        actfw_core.notify([{"message": "open file"}])

        # ファイルを読み込んでカウントアップ
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            last_count = data["count"]
            last_date = data["datetime"]
            # 現在の状態を通知
            actfw_core.notify(
                [{"message": f"Count: {last_count}, last_date: {last_date}"}]
            )
            data["count"] += 1
            data["datetime"] = datetime.now().isoformat()

        actfw_core.notify([{"message": "write file"}])

        # 更新したデータを保存
        with open(FILE_PATH, "w") as f:
            json.dump(data, f)
            actfw_core.notify([{"message": f"file updated: {FILE_PATH}"}])

        while True:
            sleep(1)
            if not self._is_running():
                break


def main():
    # Actcast application
    app = actfw_core.Application()

    cmd = actfw_core.CommandServer()
    actfw_core.notify([{"message": "start up"}])

    app.register_task(cmd)
    app.register_task(WritingFileTask())

    app.run()


if __name__ == "__main__":
    main()
