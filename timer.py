class Timer(object):

    def __init__(self, app):

        self.delay = 0
        self.app = app  # will invoke app.timedout(self) on timeout


    def start(self, delay=None):
        pass  # start the timer


    def stop(self):
        pass
