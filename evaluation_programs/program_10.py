def log_message(msg):
    print(str(msg))
class Logger():
    def notify(self):
        log_message("Alert triggered!")
logger = Logger()
logger.notify()