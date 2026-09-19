import logging

class LoggerAdapter:
	def __init__(self, logger=None):
		self._logger = logger

	def info(self, msg, *args):
		if self._logger:
			self._logger.info(msg, *args)
		else:
			print(msg % args if args else msg)

	def warning(self, msg, *args):
		if self._logger:
			self._logger.warning(msg, *args)
		else:
			print(f"WARNING: {msg % args if args else msg}")

	def error(self, msg, *args):
		if self._logger:
			self._logger.error(msg, *args)
		else:
			print(f"ERROR: {msg % args if args else msg}")


# usage example: 
# logger = LoggerAdapter(logging.getLogger(__name__)) , for real logging with logging module
# logger = LoggerAdapter() , for simple print logging

logger = LoggerAdapter()