# AppSession is a container-like object holding a running BounceRL app.
# For each running instance of an app, app session holds a data folder, a virtual
# desktop, and a process.


class AppSession:
    def __init__(self):
        self._desktop = None
        self._folder = None
        self._process = None
        self._time_controller = None

    @property
    def desktop(self):
        return self._desktop

    @property
    def data_folder(self):
        return self._folder

    @property
    def process(self):
        return self._process

    @property
    def time_controller(self):
        return self._time_controller
