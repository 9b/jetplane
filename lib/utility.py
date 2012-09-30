class utility:
	'''
	Utility class to provide static methods for all classes
	'''
	
	@staticmethod
	def logger(handler,level):
		'''
		Get a logging instance
		@param	handler	name of the logging instance
		@param	level	level in which to log
		@return	logging	object used for later on
		'''
		import logging
		
		log = logging.getLogger(handler)
		if level == "INFO":
			logging.basicConfig(level=logging.INFO)
		elif level == "DEBUG":
			logging.basicConfig(level=logging.DEBUG)
		elif level == "ERROR":
			logging.basicConfig(level=logging.ERROR)
		else:
			pass
			
		return log
