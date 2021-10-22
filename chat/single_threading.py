#!/usr/bin/python
#-*- coding: utf-8 -*- 
"""
    Single Threads 
    Esta clase permite ejecutar threads y almacenarnos, de forma que no pueda haber ejecutandose simultaneamente, dos threads con la misma clave.
    La funcion que se pase como parametro, debe recibir un parametro thread y llamar al metodo thread.is_running() para checkear si se ha ordenado 
    detener el hilo
"""
import threading 
import logging 
import time
import string
import random
logging.basicConfig(level=logging.INFO, format=' %(asctime)s ##> %(levelname)s -%(module)s.%(filename)s [%(lineno)s] %(message)s')
logger = logging.getLogger(__name__) 

TH_STOPED = "stoped"
TH_FINISHED = "finished"
TH_EXCP = "exception"

class SingleThread(threading.Thread):
    
    INSTANCES = {}
    
  
    def __init__(self, key, func , args ):
        threading.Thread.__init__(self)
        
        self._func = func
        self._args = args
        self._key = key
        self._identifier = self.__generate_id()
        self._excp = None
        self._result = None
        self._daemonic = True
        self._status = TH_FINISHED

    def __generate_id(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for i in range(20))
    
    
    def __clean_instances(self):
        key = self._key
        if key in SingleThread.INSTANCES:
            try:
                for identifiers in SingleThread.INSTANCES[key].keys():
                    prev_instance = SingleThread.INSTANCES[key].get(identifiers, None)
                    if prev_instance:
                        while prev_instance.is_running():
                            prev_instance.stop()
            except Exception as e:
                logger.error(str(e))

        else:
            SingleThread.INSTANCES[key]={}
        
        SingleThread.INSTANCES[key][self._identifier]=self
        
        self._running = False
    
    def __delete(self):
        try:
            del self._func, self._args , self._kwargs
            del SingleThread.INSTANCES[self._key][self._identifier]
        except Exception as e:
            logger.error(str(e))
    
    def is_running(self):
        return self._running

    def run(self):
        try:
            self.__clean_instances()
            self._running= True
            self._result = self._func(*self._args, thread=self)
        except Exception as e:
            logger.error(str(e))
            self._status = TH_EXCP
            self._excp = str(e)
        
        self._running=False
        self.__delete()

    def count_instances(self):
        try:
            items = SingleThread.INSTANCES[self._key].keys()
            items = items
            return len(items)
        except Exception as e:
            logger.error(str(e))
            return 0

    def whoami(self):
        return {'key': self._key, 'identifier': self._identifier}

    def stop(self):
        self._running = False
        self._status = TH_STOPED

    def get_status(self):
        return self._status

    def get_excp(self):
        return self._excp

    def get_result(self):
        return self._result



