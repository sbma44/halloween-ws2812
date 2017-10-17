import time
import socket
import asyncio
import concurrent.futures

HOSTS = {}
PORT = 2323

"""
Scans an IP for a response on the set port; records & returns it as appropriate. Run in parallel.
"""
def scan(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        result = sock.connect_ex((ip, PORT))
        if result == 0:
            address = sock.recv(1024)
            sock.close()
            return (True, ip, address.decode('ascii'))
        else:
            return (False, ip)
    except:
        return (False, ip)

"""
Send lua code to a given chipid for immediate execution
"""
def send_code(chipid, code):
    if not chipid in HOSTS:
        raise Exception("UnknownChipID: {}".format(chipid))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((HOSTS[chipid], PORT))
        if result == 0:
            sock.send(bytes(code + "\n", "ascii"))
            sock.close()
            return True
        else:
            return False
    except:
        return False

if __name__ == "__main__":
    print("Scanning for hosts with port {} open...".format(PORT))
    with concurrent.futures.ThreadPoolExecutor(1000) as ex:
        # @TODO: figure out the actual subnet instead of hardcoding
        fut = ex.map(scan, ["192.168.1.{}".format(x) for x in range(0, 256)])
        for f in fut:
            if f[0]:
                HOSTS[f[2]] = f[1]
                print("  - found host: {} / chipid: {}".format(f[1], f[2])) 

    res = send_code(list(HOSTS.keys())[0], "PROOF_OF_LIFE = \"{}\"\n".format(str(time.time())))
