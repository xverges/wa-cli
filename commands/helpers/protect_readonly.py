import errno
from functools import wraps
import inspect
import os
import sys

from .cfg import WACLI_FOLDER, READONLY_SERVICES


def protect_readonly(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        apikey = inspect.getcallargs(f, *args, **kwds).get('apikey', '')
        folder = inspect.getcallargs(f, *args, **kwds)['ctx'].obj['project_folder']
        if apikey:
            readonly_file = os.path.join(folder, WACLI_FOLDER, READONLY_SERVICES)
            if not os.path.isfile(readonly_file):
                msg = 'Missing configuration file required for this operation'
                sys.exit(FileNotFoundError(errno.ENOENT, msg, readonly_file))
            with open(readonly_file, 'r', encoding='utf-8') as cfg_file:
                for line in cfg_file.readlines():
                    if apikey in line:
                        msg = f'Service with apikey "{apikey}" is write-protected'
                        sys.exit(PermissionError(errno.EACCES, msg, readonly_file))
        return f(*args, **kwds)
    return wrapper
