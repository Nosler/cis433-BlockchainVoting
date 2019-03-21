# Sam Champer
# Very simply logger.

logging = False

def init_logger():
    global logging
    logging = True

def log(*args, **kwargs):
    if logging:
        print("LOG::", end="")
        print(*args, **kwargs)
