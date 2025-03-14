from time import sleep
import actfw_core 
from actfw_core.task.task import Task
import subprocess

FILE_PATH = "/mnt/cache_volume/cachced_file"

class WritingFileTask(Task):
    def run(self):
        subprocess.run(["touch", FILE_PATH], check=True)
        count = 0
        while True:
            with open(FILE_PATH, "a") as f:
                f.write(f"{count}\n")
            count += 1
            # read file
            with open(FILE_PATH, "r") as f:
                actfw_core.notify([{ "message": f.read() }])
            sleep(10)
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
