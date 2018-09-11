from pythonlsf import lsf

def connect(queue="batch"):
    if lsf.lsb_init(queue) > 0:
        print("Couldn't connect.")

