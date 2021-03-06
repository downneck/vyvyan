# Copyright 2015 WebEffects Network, Inc.
#
import os
import sys
import logging


# error class for the common module
class VyvyanCommonError(Exception):
    pass


class VyvyanCommon(object):
    """
    Common methods utilised by multiple vyvyan modules 
    """
    def __init__(self, cfg):
        self.cfg = cfg

    def check_num_opt_args(self, query, module, call):
        """
        [description]
        check the number of arguments in query against known max/min
 
        [parameter info]
            required:
                query: the query being passed to the module call 
                module: the module we're being called from
                call: the function we're being called from
 
        [return]
        no return. Raises an error if too may or too few arguments are supplied 
        """
        numargs = len(query.keys())
        minargs = 0
        if 'args' in self.cfg.module_metadata[module].metadata['methods'][call]['required_args'].keys():
            minargs += len(self.cfg.module_metadata[module].metadata['methods'][call]['required_args']['args'].keys())
        if 'max' in self.cfg.module_metadata[module].metadata['methods'][call]['optional_args']:
            maxargs = minargs + self.cfg.module_metadata[module].metadata['methods'][call]['optional_args']['max']
        else:
            maxargs = minargs 
        if 'min' in self.cfg.module_metadata[module].metadata['methods'][call]['optional_args']:
            minargs += self.cfg.module_metadata[module].metadata['methods'][call]['optional_args']['min']
        if numargs > maxargs:
            raise VyvyanCommonError("Please supply no more than %s optional arguments" % self.cfg.module_metadata[module].metadata['methods'][call]['optional_args']['max'])
        elif numargs < minargs:
            raise VyvyanCommonError("Please supply no fewer than %s optional arguments" % self.cfg.module_metadata[module].metadata['methods'][call]['optional_args']['min'])


    def get_valid_qkeys(self, module, call):
        """
        [description]
        collect our list of valid query keys
 
        [parameter info]
            required:
                module: the module we're being called from
                call: the function we're being called from
 
        [return]
        Returns a list of valid query keys for this module/call
        """
        valid_qkeys = []
        if 'args' in self.cfg.module_metadata[module].metadata['methods'][call]['required_args'].keys():
            for i in self.cfg.module_metadata[module].metadata['methods'][call]['required_args']['args'].keys():
                valid_qkeys.append(i)
        if 'args' in self.cfg.module_metadata[module].metadata['methods'][call]['optional_args'].keys():
            for i in self.cfg.module_metadata[module].metadata['methods'][call]['optional_args']['args'].keys():
                valid_qkeys.append(i)
        if not 'args' in self.cfg.module_metadata[module].metadata['methods'][call]['optional_args'].keys() and not 'args' in self.cfg.module_metadata[module].metadata['methods'][call]['required_args'].keys():
            valid_qkeys = None
        return valid_qkeys


    def multikeysort(self, items, columns):
        """
        [description]
        sort a list of dictionaries by multiple dictionary columns

        [parameter info]
            required:
                items: the list of dicts
                columns: a list of the keys to sort by in order of sorting

        [return]
        returns the sorted list of dicts
        """
        from operator import itemgetter
        comparers = [ ((itemgetter(col[1:].strip()), -1) if col.startswith('-') else (itemgetter(col.strip()), 1)) for col in columns]
        def comparer(left, right):
            for fn, mult in comparers:
                result = cmp(fn(left), fn(right))
                if result:
                    return mult * result
            else:
                return 0
        return sorted(items, cmp=comparer)


class VyvyanLogger(object):
    """
    Vyvyan logger class
    """
    def __init__(self, cfg):
        if not os.path.exists(cfg.logdir):
            os.mkdir(cfg.logdir)

        # create a new logger to not conflict with any logging instance
        logger = logging.getLogger('vyvyan')

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # if we're asked to log to a file, set up both the file
        if cfg.log_to_file:
            filehandler = logging.FileHandler(filename=cfg.logdir+'/'+cfg.logfile, mode='a')
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)

        # if we're asked to log to console, set up the stdout
        if cfg.log_to_console:
            stdouthandler = logging.StreamHandler(sys.stdout)
            stdouthandler.setFormatter(formatter)
            logger.addHandler(stdouthandler)

        # set the default log level
        if cfg.log_level:
            try:
                level = getattr(logging, cfg.log_level.upper())
                logger.setLevel(level)
            except Exception, e:
                raise VyvyanCommonError("bad log_level in yaml! Error: %s" % e)
        else:
            logger.setLevel(logging.DEBUG)

        logger.debug("logger initialized in %s" % (cfg.logdir+'/'+cfg.logfile))

        self.logger = logger


    # to change the logger log level
    def change_log_level(self, level, logger='vyvyan'):
        """
        Change the logger level on the fly. Usually you want do that for replace
        the log level defined in the config file.
        """
        try:
            logger = logging.getLogger(logger)
            logger.setLevel(level)
        except Exception, e:
            raise VyvyanCommonError("Error changing log level: %s" % e)


    # Wrapper helper functions around the logger class
    def debug(self, message):
        self.logger.debug(message)

    def warn(self, message):
        self.logger.warn(message)

    def info(self, message):
        self.logger.info(message)
