import logging

def log_keeper(file_path):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    # logger.debug("This message is important only when debugging the program")
    # logger.info("This message just shows basic information")
    # logger.warning("This message is about something youshould pay attention to")
    # logger.error("This message helps to debug an error that occured in your program")

if __name__ == "__main__":
    log_keeper("info.log")