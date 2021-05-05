"""TODO work again on this feature

import threading
from flask_restful import Resource


class Threads(Resource):

    class Stoppable:
        def init_stop(self, title):
            Threads.add(threading.current_thread().ident, title)

        def should_stop(self):
            return Threads.should_stop(threading.current_thread().ident)

    running = {}

    @staticmethod
    def add(id, title):
        Threads.running[int(id)] = {"title": title, "stop": False}

    @staticmethod
    def _running_threads_ids():
        return list(map(lambda x: x.ident, threading.enumerate()))

    @staticmethod
    def should_stop(id):
        threads = Threads.get_threads()
        return id in threads and threads[id]["stop"]

    @staticmethod
    def get_threads():
        running_ids = Threads._running_threads_ids()
        for id in list(Threads.running.keys()):
            if id not in running_ids:
                del Threads.running[id]
        return Threads.running

    def get(self):
        return Threads.get_threads()

    def put(self, id):
        id = int(id)
        if id in Threads.running:
            Threads.running[id]["stop"] = True
"""
