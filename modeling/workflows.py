# Implements a compute pipeline.
# Will Support
#   - immediate or deferred executation
#   - timing individual stages
#   - recording stage definitions
#   - stage caching?

import time

# TODO: Move stage_outs into the Stage instances.
class Stage():
    def __init__(self, func, args):
        self.func = func
        self.args = args
        self.out = None

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self == other

    # Should get the value from the parent workflow if finished.
    # Otherwise should return a useful error message.
    def __call__(self):
        self.out = self.func(*self.args)

# TODO: Possibly implement caching.
class Workflow():
    def __init__(self, time_stages = True, immediate = True):
        self.time_stages = time_stages
        self.immediate = immediate
        self.stages = []

    # Adds the given stage to our workflow.
    def S(self, func, *args):
        stage = Stage(func, args)
        self.stages.append(stage)
        if self.immediate:
            self.RunStage(stage, len(self.stages) - 1)
        return stage

    def RunStage(self, stage, name):
        start = time.time()

        # Unpack stage argument values
        args = list(stage.args)
        for i, arg in enumerate(args):
            if isinstance(arg, Stage):
                args[i] = arg.out

        stage.out = stage.func(*args)
        end = time.time()
        if self.time_stages:
            print("Stage:", name, "took", end - start, "seconds")

    def __call__(self):
        # We've already evaluated the whole pipeline
        if self.immediate:
            return
        else:
            # We haven't implemented deferred execution yet.
            return

