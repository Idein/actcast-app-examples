from time import sleep
import actfw_core 
from actfw_core.task.task import Task
import subprocess

FILE_PATH = "/mnt/cache_volume/cachced_file"

class WritingFileTask(Task):
    def __init__(self, interval):
        super().__init__()
        self.interval = interval

    def run(self):
        subprocess.run(["touch", FILE_PATH], check=True)
        while self._is_running():
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

            # sleep
            for i in range(self.interval):
                if not self._is_running():
                    break
                sleep(1)


def main():
    # Actcast application
    app = actfw_core.Application()

    # Load act setting
    settings = app.get_settings({ 'interval': 60 })

    cmd = actfw_core.CommandServer()
    actfw_core.notify([{ "message": "start up" }])

    app.register_task(cmd)
    app.register_task(WritingFileTask(settings.get('interval', 60)))

    app.run()

if __name__ == "__main__":
    main()
