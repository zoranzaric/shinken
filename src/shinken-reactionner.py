#!/usr/bin/env python
#Copyright (C) 2009-2010 : 
#    Gabes Jean, naparuba@gmail.com 
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


#This class is an application for launch actions 
#like notifications or event handlers
#The actionner listen configuration from Arbiter in a port (first argument)
#the configuration gived by arbiter is schedulers where actionner will take 
#actions.
#When already launch and have a conf, actionner still listen to arbiter (one 
#a timeout) if arbiter wants it to have a new conf, actionner forgot old 
#chedulers (and actions into) take new ones and do the (new) job.

import sys, os
import getopt
import ConfigParser

from satellite import Satellite
from util import to_int, to_bool

VERSION = "0.1"


#Our main APP class
class Reactionner(Satellite):
	do_checks = False #I do not do checks
	do_actions = True #just actions like notifications
	#default_port = 7769

	properties = {
		'workdir' : {'default' : '/usr/local/shinken/src/var', 'pythonize' : None, 'path' : True},
		'pidfile' : {'default' : '/usr/local/shinken/src/var/reactionnerd.pid', 'pythonize' : None, 'path' : True},
		'port' : {'default' : '7769', 'pythonize' : to_int},
		'host' : {'default' : '0.0.0.0', 'pythonize' : None},
		'user' : {'default' : 'shinken', 'pythonize' : None},
		'group' : {'default' : 'shinken', 'pythonize' : None},
		'idontcareaboutsecurity' : {'default' : '0', 'pythonize' : to_bool}
		}


################### Process launch part
def usage(name):
    print "Shinken Reactionner Daemon, version %s, from :" % VERSION
    print "        Gabes Jean, naparuba@gmail.com"
    print "        Gerhard Lausser, Gerhard.Lausser@consol.de"
    print "Usage: %s [options] [-c configfile]" % name
    print "Options:"
    print " -c, --config"
    print "\tConfig file."
    print " -d, --daemon"
    print "\tRun in daemon mode"
    print " -r, --replace"
    print "\tReplace previous running scheduler"
    print " -h, --help"
    print "\tPrint detailed help screen"
    print " --debug"
    print "\tDebug File. Default : no use (why debug a bug free program? :) )"



#lets go to the party
if __name__ == "__main__":
    #Manage the options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hrdc::w", ["help", "replace", "daemon", "config=", "debug=", "easter"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(sys.argv[0])
        sys.exit(2)
    #Default params
    config_file = None
    is_daemon=False
    do_replace=False
    debug=False
    debug_file=None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(sys.argv[0])
            sys.exit()
	elif o in ("-r", "--replace"):
            do_replace = True
        elif o in ("-c", "--config"):
            config_file = a
        elif o in ("-d", "--daemon"):
            is_daemon = True
	elif o in ("--debug"):
            debug = True
	    debug_file = a
        else:
            print "Sorry, the option",o, a, "is unknown"
	    usage(sys.argv[0])
            sys.exit()


    p = Reactionner(config_file, is_daemon, do_replace, debug, debug_file)
    #import cProfile
    p.main()
    #command = """p.main()"""
    #cProfile.runctx( command, globals(), locals(), filename="var/Shinken.profile" )
