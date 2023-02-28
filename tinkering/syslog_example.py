import socket
import logging
import logging.handlers
from logging.handlers import SysLogHandler

def main():
    logger = logging.getLogger('SysLogLogger')
    logger.setLevel(logging.INFO)
    handler = SysLogHandler(facility=SysLogHandler.LOG_USER, address=('127.0.0.1', 513), socktype=socket.SOCK_STREAM)

    logger.addHandler(handler)

    formatter = logging.Formatter(
        f'%(asctime)s {socket.gethostname()} lds_dns: %(message)s',
        datefmt='%b %d %H:%M:%S'
    )
    handler.setFormatter(fmt=formatter)

    #Jan 03 03:06:39 127.0.0.1 lds_dns: 416458 - 1672715199 03/01/2023 03:06:39,52.37.159.152,64062,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN

    message =  '416458 - 1672715199 03/01/2023 03:06:39,52.37.159.152,64062,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN\n'

    logger.info(message)

if __name__ == '__main__':
    main()
