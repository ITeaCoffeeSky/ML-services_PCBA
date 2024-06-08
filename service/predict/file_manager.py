import logging

import watchdog.events
import watchdog.observers
import time

import customlib as cl

ROOT_DIR = '/home/ilya/HSE/ML-services_PCBA/service'
AOI_FILES_PATH = ROOT_DIR + '/test_files/aoi_files/'
IMG_DATA_PATH = ROOT_DIR + '/test_files/img_files_may/'
FILE_BUFFER = ROOT_DIR + '/test_files/file_buffer/'
FILE_ARCH_XML = ROOT_DIR + '/test_files/file_arch/xml/'
FILE_ARCH_IMG = ROOT_DIR + '/test_files/file_arch/img/'

# logging settings
py_logger = logging.getLogger(__name__)
py_logger.setLevel(logging.INFO)
py_handler = logging.FileHandler("./log/file_manager.log", mode='a')
py_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
py_handler.setFormatter(py_formatter)
py_logger.addHandler(py_handler)
py_logger.info(" ")
py_logger.info("############################################################")
py_logger.info("Start logging for module file_manager...")


class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        # Set the patterns for PatternMatchingEventHandler
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=['*.xml'],
                                                             ignore_directories=True, case_sensitive=False)

    def on_created(self, event):
        py_logger.info("Watchdog received created event - % s." % event.src_path)
        info, status = cl.copy_img_files(event.src_path,
                                         IMG_DATA_PATH,
                                         FILE_BUFFER,
                                         FILE_ARCH_XML,
                                         FILE_ARCH_IMG)
        py_logger.info("Copy status: % s" % status)
        py_logger.info("Files: % s." % info)


if __name__ == "__main__":
    event_handler = Handler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, path=AOI_FILES_PATH, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        py_logger.info(" ")
        py_logger.info("Stopping logging for module file_manager...")
        py_logger.info("############################################################")
        observer.stop()
    observer.join()
