#!/usr/bin/env python
#Copyright (C) 2009-2011 :
#    Denis GERMAIN, dt.germain@gmail.com
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

################################################
# check_shinken.py :
#    This check is getting daemons state from
#    a arbiter connexion.
################################################

import os

# Exit statuses recognized by Nagios and thus by Shinken
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

#Name of the Pyro Object we are searching
PYRO_OBJECT = 'ForArbiter'
daemon_types = ['arbiter', 'broker', 'scheduler', 'poller', 'reactionner']

try:
    import shinken
except ImportError:
    # If importing shinken fails, try to load from current directory
    # or parent directory to support running without installation.
    # Submodules will then be loaded from there, too.
    import imp
    if not hasattr(os, "getuid") or os.getuid() != 0:
        imp.load_module('shinken', *imp.find_module('shinken', [".", ".."]))


from optparse import OptionParser
try:
    import shinken.pyro_wrapper as pyro
    from shinken.pyro_wrapper import Pyro
except ImportError, exp:
    print 'CRITICAL : check_shinken requires the Python Pyro and the shinken.pyro_wrapper module. Please install it. (%s)' % exp
    raise SystemExit, CRITICAL


def check_deamons_numbers(result, target):
    total_number = len(result)
    alive_number = len([e for e in result.values() if e['alive']])
    total_spare_number = len([e for e in result.values() if e['spare']])
    alive_spare_number = len([e for e in result.values() if e['spare'] and e['alive']])
    dead_number = total_number - alive_number
    dead_list = ','.join([n for n in result if not result[n]['alive']])
    #TODO : perfdata to graph deamons would be nice (in big HA architectures)
    #if alive_number <= critical, then we have a big problem
    if alive_number <= options.critical:
	print "CRITICAL - only %d/%d %s(s) UP. Down elements : %s" % (alive_number, total_number, target, dead_list)  
	raise SystemExit, CRITICAL
    #We are not in a case where there is no more daemons, but are there daemons down?
    elif dead_number >= options.warning:
	print "WARNING - %d/%d %s(s) DOWN :%s" % (dead_number, total_number, target, dead_list)
	raise SystemExit, WARNING
        #Everything seems fine. But that's no surprise, is it?
    else :
	print "OK - %d/%d %s(s) UP, with %d/%d spare(s) UP" % (alive_number, total_number, target, alive_spare_number, total_spare_number)
	raise SystemExit, OK

# Adding options. None are required, check_shinken will use shinken defaults
#TODO : Add more control in args problem and usage than the default OptionParser one
parser = OptionParser()
parser.add_option('-a', '--hostname', dest='hostname', default='127.0.0.1')
parser.add_option('-p', '--portnumber', dest='portnum', default=7770)
parser.add_option('-s', '--ssl', dest='ssl', default=False)
#TODO : Add a list of correct values for target and don't authorize anything else
parser.add_option('-t', '--target', dest='target')
parser.add_option('-d', '--daemonname', dest='daemon', default='')
#In HA architectures, a warning should be displayed if there's one daemon down
parser.add_option('-w','--warning', dest='warning', default = 1)
#If no deamon is left, display a critical (but shinken will be probably dead already)
parser.add_option('-c', '--critical', dest='critical', default = 0)

#Retrieving options
options, args = parser.parse_args()
#TODO : for now, helpme doesn't work as desired
options.helpme = False

# Check for required option target
if not getattr(options, 'target'):
    print 'CRITICAL - target is not specified; You must specify which daemons you want to check!'
    parser.print_help()
    raise SystemExit, CRITICAL
elif options.target not in daemon_types:
    print 'CRITICAL - target %s is not a Shinken daemon!' % options.target
    parser.print_help()
    raise SystemExit, CRITICAL

uri = pyro.create_uri(options.hostname, options.portnum, PYRO_OBJECT , options.ssl)
    
if options.daemon:
    # We just want a check for a single satellite daemon
    # Only OK or CRITICAL here
    daemon_name = options.daemon
    try:
        result = Pyro.core.getProxyForURI(uri).get_satellite_status(options.target, daemon_name)
    except Pyro.errors.ProtocolError, exp:
        print "CRITICAL : the Arbiter is not reachable : (%s)." % exp
        raise SystemExit, CRITICAL
    
    if result:
        if result['alive']:
            print 'OK - %s alive' % daemon_name
            raise SystemExit, OK
        else:
            print 'CRITICAL - %s down' % daemon_name
            raise SystemExit, CRITICAL
    else:
        print 'UNKNOWN - %s status could not be retrieved' % daemon_name
	raise SystemExit, UNKNOWN
else:
    # If no daemonname is specified, we want a general overview of the "target" daemons
    result = {}

    try:
        daemon_list = Pyro.core.getProxyForURI(uri).get_satellite_list(options.target)
    except Pyro.errors.ProtocolError, exp:
        print "CRITICAL : the Arbiter is not reachable : (%s)." % exp
        raise SystemExit, CRITICAL

    for daemon_name in daemon_list:
	# Getting individual daemon and putting status info in the result dictionnary
        try:
            result[daemon_name] = Pyro.core.getProxyForURI(uri).get_satellite_status(options.target, daemon_name)
        except Pyro.errors.ProtocolError, exp:
            print "CRITICAL : the Arbiter is not reachable : (%s)." % exp
            raise SystemExit, CRITICAL

    # Now we have all data
    if result:
	check_deamons_numbers(result, options.target)
    else :
	print 'UNKNOWN - Arbiter could not retrieve status for %s' % options.target
	raise SystemExit, UNKNOWN
