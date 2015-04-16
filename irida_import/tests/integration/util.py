import time
import socket


def wait_until_up(address, port, timeout):
    """
    Wait until a port at an address is occupied, or time out

    :type address: str
    :param address: e.g. 'localhost' or '127.0.0.1'
    :type prot: int
    :param port: e.g. 8888
    :type timeout: int
    :param timeout: the time to wait in seconds until throwing an exception
    """
    max_time = time.time() + timeout
    up = False
    while not up and time.time() < max_time:
        up = check_up(address, port)

        # If we query Galaxy immediately it may reset the connection:
        time.sleep(10)

    if not up:
        raise Exception('There was no response at {} on port {} for {} seconds'
                        .format(address, port, timeout))


def check_up(address, port):
    """
    Find out if a port at an address is occupied
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((address, port))
    sock.close()
    if result == 0:
        ans = True
    else:
        ans = False
    return ans
