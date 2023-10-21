# -*- coding: UTF-8 -*-

import logging
import logging.config
from traceback import format_exception
from sys import exc_info
from lib.Helpers import read_json
from lib.Helpers import is_sequence_with_any_elements, is_sequence
from lib.Helpers import case_normalize, wrap_str_fast
from pathlib import Path


class Logger:
	_jsoncfg = None
	_isstarted = False
	_wrap_len = None

	def __init__(self, config_file='log.json', clear_logfiles=False, wrap_len=None):
		self._wrap_len = wrap_len
		p = Path(config_file)

		if p.is_file():
			self._jsoncfg = read_json(config_file)
			if clear_logfiles:
				j = self._jsoncfg
				if is_sequence(j) and "handlers" in j:
					handlers = j["handlers"]
					for k, handler in handlers.iteritems():
						if "filename" in handler:
							p2 = Path(handler["filename"]).absolute()
							if p2.is_file():
								p2.unlink()

	def startlogger(self):
		if is_sequence(self._jsoncfg):
			logging.config.dictConfig(self._jsoncfg)
			self._isstarted = True

	@staticmethod
	def shutdown():
		logging.shutdown()

	@staticmethod
	def _get_exception_safe(exceptionerr, *trace):

		# if isinstance(exceptionerr, ReformattedException):
		# 	return case_normalize(exceptionerr.message)
		# else:
		formatted = ""
		exceptionerr_norm = "NO_MESSAGE"

		if hasattr(exceptionerr, 'args') and \
				len(exceptionerr.args) == 4 and \
				is_sequence_with_any_elements(exceptionerr.args[2]) and \
				len(exceptionerr.args[2]) == 6:
			# Possible weird, abnormal, dysmal, disfunctional windows cp1250(based on ISO-8859-2) encoded error
			exceptionerr_norm = case_normalize(exceptionerr.args[2][1]) + ": " + case_normalize(
				exceptionerr.args[2][2])
		elif hasattr(exceptionerr, 'message'):
			exceptionerr_norm = case_normalize(exceptionerr.message)

		if trace is None or (is_sequence(trace) and len(trace) == 0):
			excfmtlist = format_exception(type(exceptionerr), exceptionerr, exc_info()[2])
			for (index, excfmtitem) in enumerate(excfmtlist):
				formatted += "\r\n\t" + case_normalize(excfmtitem)
			formatted = "{}\r\n{}".format(exceptionerr_norm, formatted)
		else:
			tracestr = ""
			if is_sequence(trace):
				for t in trace:
					if is_sequence(t):
						for t2 in t:
							tracestr += "\r\n" + t2
					else:
						tracestr += "\r\n" + t
			else:
				tracestr = trace
			formatted = case_normalize("{} {}".format(exceptionerr_norm, tracestr))
		return formatted

	def is_started(self):
		return self._isstarted

	@staticmethod
	def getlogger(*args):
		if is_sequence(args):
			if len(args) > 0:
				return logging.getLogger(args[0])
			else:
				return logging.getLogger("root")
		else:
			print(type(args))

	def info(self, infotext, *args, **kwargs):
		logger = Logger.getlogger("info_logger")
		if logger is not None:
			logger.info(
				wrap_str_fast(150, infotext)
				if
				self._wrap_len is not None
				else
				infotext,
				*args, **kwargs
			)

	def error(self, errortext, *args, **kwargs):
		logger = Logger.getlogger("error_logger")
		if logger is not None:
			logger.error(
				wrap_str_fast(150, errortext)
				if
				self._wrap_len is not None
				else
				errortext,
				*args, **kwargs
			)

	@staticmethod
	def exception(exceptionerr, *args, **kwargs):
		logger = Logger.getlogger("error_logger")
		if logger is not None:
			logger.exception(exceptionerr, *args, **kwargs)

	@staticmethod
	def exception_mail(exc, *trace):
		excmsg = Logger._get_exception_safe(exc, *trace)
		logger = Logger.getlogger("mail_logger")
		logger.error(excmsg)

	# sendmail(from_addr, recipients, self._mail_smtp_server, subject,
	#          get_reformatted_exception("Schwerer Ausnahmefehler", exc),
	#          self._mail_local_hostname, self._mail_port)

	@staticmethod
	def exception_safe(exceptionerr, *trace):
		logger = Logger.getlogger("error_logger")
		if logger is not None:
			exsafe = Logger._get_exception_safe(exceptionerr, *trace)
			logger.error(exsafe)
