#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import os, errno
import logging.handlers
import inspect
import traceback
from functools import wraps

class Log:
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARN = logging.WARNING
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET
    logger = None

    @staticmethod
    def init(service_name, log_path, level="INFO", backup_count=10, file_size_in_mb=10, 
            syslog_server=None, syslog_port=None):
        """ Initialize logging to log to syslog """
        try:
            if log_path and not os.path.exists(log_path): os.makedirs(log_path)
        except OSError as err:
            if err.errno != errno.EEXIST: raise
        max_bytes = 0
        if file_size_in_mb:
            max_bytes = file_size_in_mb * 1024 * 1024
        Log.audit_logger = Log._get_logger(syslog_server, syslog_port, service_name,
                        "audit", getattr(Log, level), log_path, backup_count, max_bytes)

        Log.logger = Log._get_logger(syslog_server, syslog_port, service_name,
                       "system", getattr(Log, level), log_path, backup_count, max_bytes)

    @staticmethod
    def _get_logger(syslog_server: str, syslog_port: str, file_name: str, logger_type,
                        log_level, log_path: str, backup_count: int, max_bytes: int):
        """
        This Function Creates the Logger for Log Files.
        :param syslog_server: syslog server
        :param syslog_port: syslog port
        :param file_name: File name for Log Files. :type: Str
        :param logger_type: logging type i.e audit, system :type: Str
        :param log_level: Log Class Instance :type: Class(Log)
        :return: Logger Object
        """
        log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
        logger_name = f"{file_name}"
        formatter = logging.Formatter(log_format, "%Y-%m-%d %H:%M:%S")
        if logger_type == "audit":
            log_format = "%(name)s %(message)s"
            logger_name = f"{file_name}_audit"
            formatter = logging.Formatter(log_format)
        logger = logging.getLogger(logger_name)
        if syslog_server and syslog_port:
            log_handler = logging.handlers.SysLogHandler(address =
                                           (syslog_server, syslog_port))
            logger.setLevel(log_level)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        else:
            log_file = os.path.join(log_path, f"{file_name}.log")
            file_handler = logging.handlers.RotatingFileHandler(log_file, mode="a",
                                  maxBytes=max_bytes, backupCount=backup_count)
            file_handler.setFormatter(formatter)
            logger.setLevel(log_level)
            logger.addHandler(file_handler)
  
        return logger

    @staticmethod
    def debug(msg, *args, **kwargs):
        caller = inspect.stack()[1][3]
        Log.logger.debug(f"[{caller}] {msg}", *args, **kwargs)

    @staticmethod
    def info(msg, *args, **kwargs):
        caller = inspect.stack()[1][3]
        Log.logger.info(f"[{caller}] {msg}", *args, **kwargs)

    @staticmethod
    def audit(msg, *args, **kwargs):
        caller = inspect.stack()[1][3]
        Log.audit_logger.info(f"audit: {msg}", *args, **kwargs)

    @staticmethod
    def support_bundle(msg, *args, **kwargs):
        caller = inspect.stack()[1][3]
        Log.audit_logger.info(f"support_bundle: {msg}", *args, **kwargs)

    @staticmethod
    def warn(msg, *args, **kwargs):
        caller = inspect.stack()[1][3]
        Log.logger.warn(f"[{caller}] {msg}", *args, **kwargs)

    @staticmethod
    def error(msg, *args, **kwargs):
        caller = inspect.stack()[1][3]
        Log.logger.error(f"[{caller}] {msg}", *args, **kwargs)

    @staticmethod
    def critical(msg, *args, **kwargs):
        """ Logs a message with level CRITICAL on this logger. """
        caller = inspect.stack()[1][3]
        Log.logger.critical(traceback.format_exc())
        Log.logger.critical(f"[{caller}] {msg}", *args, **kwargs)

    @staticmethod
    def exception(e, *args, **kwargs):
        """ Logs a message with level ERROR on this logger. """
        caller = inspect.stack()[1][3]
        Log.logger.exception(f"[{caller}] [{e.__class__.__name__}] e")

    @staticmethod
    def console(msg, *args, **kwargs):
        """ Logs a message with level ERROR on this logger. """
        caller = inspect.stack()[1][3]
        Log.logger.debug(f"[{caller}] {msg}", *args, **kwargs)
        print(f"[{caller}] {msg}")


    @staticmethod
    def trace_method(level, exclude_args=[], truncate_at=80):
        """
        A wrapper method that logs each invocation and exit of the wrapped function.
        :param: level - Level of logging (e.g. Logger.DEBUG)
        :param: exclude_args - Array of arguments to exclude from the logging
                (it can be useful e.g. for hiding passwords from the log file)
        :param: truncate_at - Allows to truncate the printed argument values. 80 by default.

        Example usage:
        @Logger.trace_method(Logger.DEBUG)
        def some_function(arg_1, arg_2):
            pass
        """
        def _fmt_value(obj):
            str_value = repr(obj)
            if len(str_value) < truncate_at:
                return str_value
            else:
                return str_value[:truncate_at] + "..."

        def _print_start(func, *args, **kwargs):
            pos_args = [_fmt_value(arg) for arg in args]
            # TODO: handle exclusion of positional arguments as well
            kw_args = [key + "=" + _fmt_value(kwargs[key]) for key in kwargs
                if key not in exclude_args]

            message = "[{}] Invoked with ({})".format(
                func.__qualname__, ",".join(pos_args + kw_args))
            Log.logger.log(level, message)

        def _print_end(func, response):
            message = "[{}] Returned {}".format(func.__qualname__, _fmt_value(response))
            Log.logger.log(level, message)

        # This function will be used as a decorator
        def decorator(func):
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                _print_start(func, *args, **kwargs)
                resp = func(*args, **kwargs)
                _print_end(func, resp)
                return resp

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                _print_start(func, *args, **kwargs)
                resp = await func(*args, **kwargs)
                _print_end(func, resp)
                return resp

            # If the function is async, it needs special treatment
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator
