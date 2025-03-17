from time import sleep
import actfw_core 
from actfw_core.task.task import Task
import subprocess

FILE_PATH = "/mnt/cache_volume/cachced_file"

class WritingFileTask(Task):
    def run(self):
        subprocess.run(["touch", FILE_PATH], check=True)
        while True:
            # read count from file
            with open(FILE_PATH, "r") as f:
                content = f.read()
                actfw_core.notify([{ "message": content }])
                if content == "":
                    count = 0
                else:
                    count = int(content)

            # overwrite count to file
            with open(FILE_PATH, "w") as f:
                f.write(str(count + 1))

            sleep(60)
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
