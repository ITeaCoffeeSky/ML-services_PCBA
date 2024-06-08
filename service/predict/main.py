import logging

import watchdog.events
import watchdog.observers
import time
import requests

import customlib as cl

ROOT_DIR = '/home/ilya/HSE/ML-services_PCBA/service'
FILE_BUFFER = ROOT_DIR + '/test_files/file_buffer/'
FILE_PREDICT = ROOT_DIR + '/test_files/file_predict/'
# URL_PREDICT = 'http://predictserver:8002/predict'
URL_PREDICT = 'http://0.0.0.0:8002/predict'

# logging settings
py_logger = logging.getLogger(__name__)
py_logger.setLevel(logging.INFO)
py_handler = logging.FileHandler("./log/main.log", mode='a')
py_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
py_handler.setFormatter(py_formatter)
py_logger.addHandler(py_handler)
py_logger.info(" ")
py_logger.info("############################################################")
py_logger.info("Start logging for module main...")


class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        # Set the patterns for PatternMatchingEventHandler
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=['*.xml'],
                                                             ignore_directories=True, case_sensitive=False)

    def on_created(self, event):
        py_logger.info("Watchdog received created event - % s." % event.src_path)
        info, status, X, y = cl.get_X_y(event.src_path, FILE_BUFFER)

        if status == 'OK':
            headers = {'Content-Type': 'application/json',
                       'Accept': 'application/json'}
            data = {'X': X, 'y': y}

            response = requests.post(URL_PREDICT,
                                     json=data,
                                     headers=headers)

            if response.status_code == 200:
                y_pred = response.json()
                print("OK response: ", y_pred)

                result = []
                for idx in range(len(y_pred)):
                    result.append({X[idx]: y_pred[idx]})

                py_logger.info("Prediction values: % s" % result)
            else:
                py_logger.info("No response from predict server % s" % response.status_code)

        py_logger.info("Copy status: % s" % status)
        py_logger.info("Files: % s." % info)


if __name__ == "__main__":
    event_handler = Handler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, path=FILE_BUFFER, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        py_logger.info(" ")
        py_logger.info("Stopping logging for module main...")
        py_logger.info("############################################################")
        observer.stop()
    observer.join()
