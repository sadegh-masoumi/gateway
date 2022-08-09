from threading import Lock

def synchronized(f):
    lock = Lock()
    def func(*args, **kwargs):
        with lock:
            f(*args, **kwargs)
    return func