from time import sleep
import actfw_core 
from actfw_core.task.task import Task

class EmptyTask(Task):
    def run(self):
        while True:
            actfw_core.notify([{ "message": "EmptyTask is running" }])
            sleep(1)
            if not self._is_running():
                break


def main():
    # Actcast application
    app = actfw_core.Application()

    cmd = actfw_core.CommandServer()
    actfw_core.notify([{ "message": "start up" }])

    app.register_task(cmd)
    app.register_task(EmptyTask())

    app.run()

if __name__ == "__main__":
    main()
