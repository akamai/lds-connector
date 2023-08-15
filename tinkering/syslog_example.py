import socket
import logging
import logging.handlers
from logging.handlers import SysLogHandler

TIMESTAMP = 1672715199

def old_syslog():
    logger = logging.getLogger('SysLogLogger')
    logger.setLevel(logging.INFO)

    handler = SysLogHandler(facility=SysLogHandler.LOG_USER, address=('127.0.0.1', 514), socktype=socket.SOCK_STREAM)
    handler.append_nul = True
    handler.setFormatter(fmt=logging.Formatter(
        f'%(asctime)s 172.233.214.122 lds_dns_log: %(message)s',
        datefmt='%b %d %H:%M:%S'
    ))
    logger.addHandler(handler)

    message = '416458 - 1672715199 03/01/2023 03:06:38,52.37.159.152,64062,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN  \n'
    logger.info(message)

    print('Sent using old syslog')

def new_syslog():
    logger = logging.getLogger('SysLogLogger')
    logger.setLevel(logging.INFO)

    handler = SysLogHandler(facility=SysLogHandler.LOG_USER, address=('127.0.0.1', 514), socktype=socket.SOCK_STREAM)
    handler.append_nul = True
    handler.setFormatter(fmt=logging.Formatter(
        f'1 %(asctime)s 172.233.214.122 lds_dns_log - - - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    ))
    logger.addHandler(handler)

    message = '416458 - 1672715199 03/01/2023 03:06:38,52.37.159.152,64062,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN  \n'
    logger.info(message)

    print('Sent using new syslog')

if __name__ == '__main__':
    new_syslog()
