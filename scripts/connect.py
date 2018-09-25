from pythonlsf import lsf


def connect(queue="batch"):
    """
    Call this to connect to lsf. The name of the queue does not have to be the
    one you actually want to query, it just needs to be a valid queue.

    :param queue: (str) queue that exists in lsf.
    :return:
    """
    if lsf.lsb_init(queue) > 0:
        raise Exception("Couldn't connect.")

