#!/usr/bin/env python
#Copyright (C) 2009-2010 :
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


import os
import time

from shinken.util import to_int, to_bool
from shinken.downtime import Downtime
from shinken.contactdowntime import ContactDowntime
from shinken.comment import Comment
from shinken.objects import CommandCall
from shinken.log import logger
from shinken.pollerlink import PollerLink


class ExternalCommand:
    my_type = 'externalcommand'
    def __init__(self, cmd_line):
        self.cmd_line = cmd_line


class ExternalCommandManager:

    commands = {
        'CHANGE_CONTACT_MODSATTR' : {'global' : True, 'args' : ['contact', None]},
        'CHANGE_CONTACT_MODHATTR' : {'global' : True, 'args' : ['contact', None]},
        'CHANGE_CONTACT_MODATTR' : {'global' : True, 'args' : ['contact', None]},
        'CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD' : {'global' : True, 'args' : ['contact', 'time_period']},
        'ADD_SVC_COMMENT'  : {'global' : False, 'args' : ['service', 'to_bool', 'author', None]},
        'ADD_HOST_COMMENT' : {'global' : False, 'args' : ['host', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_SVC_PROBLEM' : {'global' : False, 'args' : ['service' , 'to_int', 'to_bool', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_HOST_PROBLEM' : {'global' : False, 'args' : ['host', 'to_int', 'to_bool', 'to_bool', 'author', None]},
        'CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD' : {'global' : True, 'args' : ['contact', 'time_period']},
        'CHANGE_CUSTOM_CONTACT_VAR' : {'global' : True, 'args' : ['contact', None,None]},
        'CHANGE_CUSTOM_HOST_VAR' : {'global' : False, 'args' : ['host', None,None]},
        'CHANGE_CUSTOM_SVC_VAR' : {'global' : False, 'args' : ['service', None,None]},
        'CHANGE_GLOBAL_HOST_EVENT_HANDLER' : {'global' : True, 'args' : ['command']},
        'CHANGE_GLOBAL_SVC_EVENT_HANDLER' : {'global' : True, 'args' : ['command']},
        'CHANGE_HOST_CHECK_COMMAND' : {'global' : False, 'args' : ['host', 'command']},
        'CHANGE_HOST_CHECK_TIMEPERIOD' : {'global' : False, 'args' : ['host', 'time_period']},
        'CHANGE_HOST_EVENT_HANDLER' : {'global' : False, 'args' : ['host', 'command']},
        'CHANGE_HOST_MODATTR' : {'global' : False, 'args' : ['host', 'to_int']},
        'CHANGE_MAX_HOST_CHECK_ATTEMPTS': {'global' : False, 'args' : ['host', 'to_int']},
        'CHANGE_MAX_SVC_CHECK_ATTEMPTS' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_NORMAL_HOST_CHECK_INTERVAL' : {'global' : False, 'args' : ['host', 'to_int']},
        'CHANGE_NORMAL_SVC_CHECK_INTERVAL' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_RETRY_HOST_CHECK_INTERVAL' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_RETRY_SVC_CHECK_INTERVAL' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_SVC_CHECK_COMMAND' : {'global' : False, 'args' : ['service', 'command']},
        'CHANGE_SVC_CHECK_TIMEPERIOD' : {'global' : False, 'args' : ['service', 'time_period']},
        'CHANGE_SVC_EVENT_HANDLER' : {'global' : False, 'args' : ['service', 'command']},
        'CHANGE_SVC_MODATTR' : {'global' : False, 'args' : ['service', 'to_int']},
        'CHANGE_SVC_NOTIFICATION_TIMEPERIOD' : {'global' : False, 'args' : ['service', 'time_period']},
        'DELAY_HOST_NOTIFICATION' : {'global' : False, 'args' : ['host', 'to_int']},
        'DELAY_SVC_NOTIFICATION' : {'global' : False, 'args' : ['service', 'to_int']},
        'DEL_ALL_HOST_COMMENTS' : {'global' : False, 'args' : ['host']},
        'DEL_ALL_SVC_COMMENTS' : {'global' : False, 'args' : ['service']},
        'DEL_CONTACT_DOWNTIME' : {'global' : True, 'args' : ['to_int']},
        'DEL_HOST_COMMENT' : {'global' : True, 'args' : ['to_int']},
        'DEL_HOST_DOWNTIME' : {'global' : True, 'args' : ['to_int']},
        'DEL_SVC_COMMENT' : {'global' : True, 'args' : ['to_int']},
        'DEL_SVC_DOWNTIME' : {'global' : True, 'args' : ['to_int']},
        'DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST' : {'global' : False, 'args' : ['host']},
        'DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['contact_group']},
        'DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['contact_group']},
        'DISABLE_CONTACT_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['contact']},
        'DISABLE_CONTACT_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['contact']},
        'DISABLE_EVENT_HANDLERS' : {'global' : True, 'args' : []},
        'DISABLE_FAILURE_PREDICTION' : {'global' : True, 'args' : []},
        'DISABLE_FLAP_DETECTION' : {'global' : True, 'args' : []},
        'DISABLE_HOSTGROUP_HOST_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_SVC_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOSTGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['host_group']},
        'DISABLE_HOST_AND_CHILD_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_CHECK' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_EVENT_HANDLER' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_FLAP_DETECTION' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_FRESHNESS_CHECKS' : {'global' : True, 'args' : []},
        'DISABLE_HOST_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_SVC_CHECKS' : {'global' : False, 'args' : ['host']},
        'DISABLE_HOST_SVC_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'DISABLE_NOTIFICATIONS' : {'global' : True, 'args' : []},
        'DISABLE_PASSIVE_HOST_CHECKS' : {'global' : False, 'args' : ['host']},
        'DISABLE_PASSIVE_SVC_CHECKS' : {'global' : False, 'args' : ['service']},
        'DISABLE_PERFORMANCE_DATA' : {'global' : True, 'args' : []},
        'DISABLE_SERVICEGROUP_HOST_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_SVC_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['service_group']},
        'DISABLE_SERVICE_FLAP_DETECTION' : {'global' : False, 'args' : ['service']},
        'DISABLE_SERVICE_FRESHNESS_CHECKS' : {'global' : True, 'args' : []},
        'DISABLE_SVC_CHECK' : {'global' : False, 'args' : ['service']},
        'DISABLE_SVC_EVENT_HANDLER' : {'global' : False, 'args' : ['service']},
        'DISABLE_SVC_FLAP_DETECTION' : {'global' : False, 'args' : ['service']},
        'DISABLE_SVC_NOTIFICATIONS' : {'global' : False, 'args' : ['service']},
        'ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST' : {'global' : False, 'args' : ['host']},
        'ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['contact_group']},
        'ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['contact_group']},
        'ENABLE_CONTACT_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['contact']},
        'ENABLE_CONTACT_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['contact']},
        'ENABLE_EVENT_HANDLERS' : {'global' : True, 'args' : []},
        'ENABLE_FAILURE_PREDICTION' : {'global' : True, 'args' : []},
        'ENABLE_FLAP_DETECTION' : {'global' : True, 'args' : []},
        'ENABLE_HOSTGROUP_HOST_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_SVC_CHECKS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOSTGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['host_group']},
        'ENABLE_HOST_AND_CHILD_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_CHECK' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_EVENT_HANDLER' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_FLAP_DETECTION' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_FRESHNESS_CHECKS' : {'global' : True, 'args' : []},
        'ENABLE_HOST_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_SVC_CHECKS' : {'global' : False, 'args' : ['host']},
        'ENABLE_HOST_SVC_NOTIFICATIONS' : {'global' : False, 'args' : ['host']},
        'ENABLE_NOTIFICATIONS' : {'global' : True, 'args' : []},
        'ENABLE_PASSIVE_HOST_CHECKS' : {'global' : False, 'args' : ['host']},
        'ENABLE_PASSIVE_SVC_CHECKS' : {'global' : False, 'args' : ['service']},
        'ENABLE_PERFORMANCE_DATA' : {'global' : True, 'args' : []},
        'ENABLE_SERVICEGROUP_HOST_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_SVC_CHECKS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS' : {'global' : True, 'args' : ['service_group']},
        'ENABLE_SERVICE_FRESHNESS_CHECKS' : {'global' : True, 'args' : []},
        'ENABLE_SVC_CHECK': {'global' : False, 'args' : ['service']},
        'ENABLE_SVC_EVENT_HANDLER' : {'global' : False, 'args' : ['service']},
        'ENABLE_SVC_FLAP_DETECTION' : {'global' : False, 'args' : ['service']},
        'ENABLE_SVC_NOTIFICATIONS' : {'global' : False, 'args' : ['service']},
        'PROCESS_FILE' : {'global' : True, 'args' : [None, 'to_bool']},
        'PROCESS_HOST_CHECK_RESULT' : {'global' : False, 'args' : ['host', 'to_int', None]},
        'PROCESS_SERVICE_CHECK_RESULT' : {'global' : False, 'args' : ['service', 'to_int', None]},
        'READ_STATE_INFORMATION' : {'global' : True, 'args' : []},
        'REMOVE_HOST_ACKNOWLEDGEMENT' : {'global' : False, 'args' : ['host']},
        'REMOVE_SVC_ACKNOWLEDGEMENT' : {'global' : False, 'args' : ['service']},
        'RESTART_PROGRAM' : {'global' : True, 'args' : []},
        'SAVE_STATE_INFORMATION' : {'global' : True, 'args' : []},
        'SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME' : {'global' : False, 'args' : ['host', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author',None]},
        'SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME' : {'global' : False, 'args' : ['host', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_CONTACT_DOWNTIME' : {'global' : True, 'args' : ['contact', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_FORCED_HOST_CHECK' : {'global' : False, 'args' : ['host', 'to_int']},
        'SCHEDULE_FORCED_HOST_SVC_CHECKS' : {'global' : False, 'args' : ['host', 'to_int']},
        'SCHEDULE_FORCED_SVC_CHECK' : {'global' : False, 'args' : ['service', 'to_int']},
        'SCHEDULE_HOSTGROUP_HOST_DOWNTIME' : {'global' : True, 'args' : ['host_group', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author',None]},
        'SCHEDULE_HOSTGROUP_SVC_DOWNTIME' : {'global' : True, 'args' : ['host_group', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author',None]},
        'SCHEDULE_HOST_CHECK' : {'global' : False, 'args' : ['host', 'to_int']},
        'SCHEDULE_HOST_DOWNTIME' : {'global' : False, 'args' : ['host', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_HOST_SVC_CHECKS' : {'global' : False, 'args' : ['host', 'to_int']},
        'SCHEDULE_HOST_SVC_DOWNTIME' : {'global' : False, 'args' : ['host', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SERVICEGROUP_HOST_DOWNTIME' : {'global' : True, 'args' : ['service_group', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SERVICEGROUP_SVC_DOWNTIME' : {'global' : True, 'args' : ['service_group', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SVC_CHECK' : {'global' : False, 'args' : ['service', 'to_int']},
        'SCHEDULE_SVC_DOWNTIME' : {'global' : False, 'args' : ['service', 'to_int', 'to_int', 'to_bool', 'to_int', 'to_int', 'author', None]},
        'SEND_CUSTOM_HOST_NOTIFICATION' : {'global' : False, 'args' : ['host', 'to_int', 'author', None]},
        'SEND_CUSTOM_SVC_NOTIFICATION' : {'global' : False, 'args' : ['service', 'to_int', 'author', None]},
        'SET_HOST_NOTIFICATION_NUMBER' : {'global' : False, 'args' : ['host', 'to_int']},
        'SET_SVC_NOTIFICATION_NUMBER' : {'global' : False, 'args' : ['service', 'to_int']},
        'SHUTDOWN_PROGRAM' : {'global' : True, 'args' : []},
        'START_ACCEPTING_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : []},
        'START_ACCEPTING_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : []},
        'START_EXECUTING_HOST_CHECKS' : {'global' : True, 'args' : []},
        'START_EXECUTING_SVC_CHECKS' : {'global' : True, 'args' : []},
        'START_OBSESSING_OVER_HOST' : {'global' : False, 'args' : ['host']},
        'START_OBSESSING_OVER_HOST_CHECKS' : {'global' : True, 'args' : []},
        'START_OBSESSING_OVER_SVC' : {'global' : False, 'args' : ['service']},
        'START_OBSESSING_OVER_SVC_CHECKS' : {'global' : True, 'args' : []},
        'STOP_ACCEPTING_PASSIVE_HOST_CHECKS' : {'global' : True, 'args' : []},
        'STOP_ACCEPTING_PASSIVE_SVC_CHECKS' : {'global' : True, 'args' : []},
        'STOP_EXECUTING_HOST_CHECKS' : {'global' : True, 'args' : []},
        'STOP_EXECUTING_SVC_CHECKS' : {'global' : True, 'args' : []},
        'STOP_OBSESSING_OVER_HOST' : {'global' : False, 'args' : ['host']},
        'STOP_OBSESSING_OVER_HOST_CHECKS' : {'global' : True, 'args' : []},
        'STOP_OBSESSING_OVER_SVC' : {'global' : False, 'args' : ['service']},
        'STOP_OBSESSING_OVER_SVC_CHECKS' : {'global' : True, 'args' : []},
        'LAUNCH_SVC_EVENT_HANDLER' : {'global' : False, 'args' : ['service']},
        'LAUNCH_HOST_EVENT_HANDLER' : {'global' : False, 'args' : ['host']},
        # Now internal calls
        'ADD_SIMPLE_HOST_DEPENDENCY' : {'global' : False, 'args' : ['host', 'host']},
        'DEL_HOST_DEPENDENCY' : {'global' : False, 'args' : ['host', 'host']},
        'ADD_SIMPLE_POLLER' : {'global' : True, 'internal' : True, 'args' : [None, None, None, None]},
    }


    def __init__(self, conf, mode):
        self.mode = mode
        self.conf = conf
        self.hosts = conf.hosts
        self.services = conf.services
        self.contacts = conf.contacts
        self.hostgroups = conf.hostgroups
        self.commands = conf.commands
        self.servicegroups = conf.servicegroups
        self.contactgroups = conf.contactgroups
        self.timeperiods = conf.timeperiods
        self.pipe_path = conf.command_file
        self.fifo = None
        self.cmd_fragments = ''
        if self.mode == 'dispatcher':
            self.confs = conf.confs


    def load_scheduler(self, scheduler):
        self.sched = scheduler

    def load_arbiter(self, arbiter):
        self.arbiter = arbiter


    def open(self):
        #At the first open del and create the fifo
        if self.fifo is None:
            if os.path.exists(self.pipe_path):
                os.unlink(self.pipe_path)

            if not os.path.exists(self.pipe_path):
                os.umask(0)
                try :
                    os.mkfifo(self.pipe_path, 0660)
                    open(self.pipe_path, 'w+', os.O_NONBLOCK)
                except OSError , exp:
                    print "Error : pipe creation failed (",self.pipe_path,')', exp
                    return None
        self.fifo = os.open(self.pipe_path, os.O_NONBLOCK)
        return self.fifo


    def get(self):
        buf = os.read(self.fifo, 8096)
        r = []
        fullbuf = len(buf) == 8096 and True or False
        # If the buffer ended with a fragment last time, prepend it here
        buf = self.cmd_fragments + buf
        buflen = len(buf)
        self.cmd_fragments = ''
        if fullbuf and buf[-1] != '\n':
            # The buffer was full but ends with a command fragment
            r.extend([ExternalCommand(s) for s in (buf.split('\n'))[:-1] if s])
            self.cmd_fragments = (buf.split('\n'))[-1]
        elif buflen:
            # The buffer is either half-filled or full with a '\n' at the end.
            r.extend([ExternalCommand(s) for s in buf.split('\n') if s])
        else:
            # The buffer is empty. We "reset" the fifo here. It will be
            # re-opened in the main loop.
            os.close(self.fifo)
        return r


    def resolve_command(self, excmd):
        command = excmd.cmd_line

        # Strip and get utf8 only strings
        command = command.strip()

        #Only log if we are in the Arbiter
        if self.mode == 'dispatcher':
            logger.log('EXTERNAL COMMAND: '+command.rstrip())
        self.get_command_and_args(command)


    #Ok the command is not for every one, so we search
    #by the hostname which scheduler have the host. Then send
    #it the command
    def search_host_and_dispatch(self, host_name, command):
        print "Calling search_host_and_dispatch", 'for', host_name
        for cfg in self.confs.values():
            if cfg.hosts.find_by_name(host_name) is not None:
                print "Host", host_name, "found in a configuration"
                if cfg.is_assigned :
                    sched = cfg.assigned_to
                    print "Sending command to the scheduler", sched.get_name()
                    sched.run_external_command(command)
                else:
                    print "Problem: a configuration is found, but is not assigned!"
            else:
                logger.log("Warning:  Passive check result was received for host '%s', but the host could not be found!" % host_name)
                #print "Sorry but the host", host_name, "was not found"


    #The command is global, so sent it to every schedulers
    def dispatch_global_command(self, command):
        for sched in self.conf.schedulerlinks:
            print "Sending a command", command, 'to scheduler', sched
            if sched.alive:
                sched.run_external_command(command)


    #We need to get the first part, the command name
    def get_command_and_args(self, command):
        print "Trying to resolve", command
        command = command.rstrip()
        elts = command.split(';') # danger!!! passive checkresults with perfdata
        part1 = elts[0]

        elts2 = part1.split(' ')
        print "Elts2:", elts2
        if len(elts2) != 2:
            print "Malformed command", command
            return None
        c_name = elts2[1]

        print "Get command name", c_name
        if c_name not in ExternalCommandManager.commands:
            print "This command is not recognized, sorry"
            return None

        # Split again based on the number of args we expect. We cannot split
        # on every ; because this character may appear in the perfdata of
        # passive check results.
        entry = ExternalCommandManager.commands[c_name]
        
        #Look if the command is purely internal or not
        internal = False
        if 'internal' in entry and entry['internal']:
            internal = True

        numargs = len(entry['args'])
        if numargs and 'service' in entry['args']:
            numargs += 1
        elts = command.split(';', numargs) 

        print self.mode, entry['global']
        if self.mode == 'dispatcher' and entry['global']:
            if not internal:
                print "This command is a global one, we resent it to all schedulers"
                self.dispatch_global_command(command)
                return None

        print "Is global?", c_name, entry['global']
        print "Mode:", self.mode
        print "This command have arguments:", entry['args'], len(entry['args'])

        args = []
        i = 1
        in_service = False
        tmp_host = ''
        try:
            for elt in elts[1:]:
                print "Searching for a new arg:", elt, i
                val = elt.strip()
                if val[-1] == '\n':
                    val = val[:-1]

                print "For command arg", val

                if not in_service:
                    type_searched = entry['args'][i-1]
                    print "Search for a arg", type_searched

                    if type_searched == 'host':
                        if self.mode == 'dispatcher':
                            self.search_host_and_dispatch(val, command)
                            return None
                        h = self.hosts.find_by_name(val)
                        if h is not None:
                            args.append(h)

                    elif type_searched == 'contact':
                        c = self.contacts.find_by_name(val)
                        if c is not None:
                            args.append(c)

                    elif type_searched == 'time_period':
                        t = self.timeperiods.find_by_name(val)
                        if t is not None:
                            args.append(t)

                    elif type_searched == 'to_bool':
                        args.append(to_bool(val))

                    elif type_searched == 'to_int':
                        args.append(to_int(val))

                    elif type_searched in ('author', None):
                        args.append(val)

                    elif type_searched == 'command':
                        c = self.commands.find_cmd_by_name(val)
                        if c is not None:
                            args.append(val)#the find will be redone by
                            #the commandCall creation, but != None
                            #is usefull so a bad command will be catch

                    elif type_searched == 'host_group':
                        hg = self.hostgroups.find_by_name(val)
                        if hg is not None:
                            args.append(hg)

                    elif type_searched == 'service_group':
                        sg = self.servicegroups.find_by_name(val)
                        if sg is not None:
                            args.append(sg)

                    elif type_searched == 'contact_group':
                        cg = self.contact_groups.find_by_name(val)
                        if cg is not None:
                            args.append(cg)

                    #special case: service are TWO args host;service, so one more loop
                    #to get the two parts
                    elif type_searched == 'service':
                        in_service = True
                        tmp_host = elt.strip()
                        print "TMP HOST", tmp_host
                        if tmp_host[-1] == '\n':
                            tmp_host = tmp_host[:-1]
                            #If
                        if self.mode == 'dispatcher':
                            self.search_host_and_dispatch(tmp_host, command)
                            return None

                    i += 1
                else:
                    in_service = False
                    srv_name = elt
                    if srv_name[-1] == '\n':
                        srv_name = srv_name[:-1]
                    print "Got service full", tmp_host, srv_name
                    s = self.services.find_srv_by_name_and_hostname(tmp_host, srv_name)
                    if s is not None:
                        args.append(s)
                    else: #error, must be logged
                        logger.log("Warning: a command was received for service '%s' on host '%s', but the service could not be found!" % (srv_name, tmp_host))

        except IndexError:
            print "Sorry, the arguments are not corrects"
            return None
        print 'Finally got ARGS:', args
        if len(args) == len(entry['args']):
            print "OK, we can call the command", c_name, "with", args
            f = getattr(self, c_name)
            apply(f, args)
        else:
            print "Sorry, the arguments are not corrects", args



    #CHANGE_CONTACT_MODSATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODSATTR(self, contact, value):
        pass

    #CHANGE_CONTACT_MODHATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODHATTR(self, contact, value):
        pass

    #CHANGE_CONTACT_MODATTR;<contact_name>;<value>
    def CHANGE_CONTACT_MODATTR(self, contact, value):
        pass

    #CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD;<contact_name>;<notification_timeperiod>
    def CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD(self, contact, notification_timeperiod):
        contact.host_notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(contact)

    #ADD_SVC_COMMENT;<host_name>;<service_description>;<persistent>;<author>;<comment>
    def ADD_SVC_COMMENT(self, service, persistent, author, comment):
        c = Comment(service, persistent, author, comment, 2, 1, 1, False, 0)
        service.add_comment(c)
        self.sched.add(c)

    #ADD_HOST_COMMENT;<host_name>;<persistent>;<author>;<comment>
    def ADD_HOST_COMMENT(self, host, persistent, author, comment):
        c = Comment(host, persistent, author, comment, 1, 1, 1, False, 0)
        host.add_comment(c)
        self.sched.add(c)

    #ACKNOWLEDGE_SVC_PROBLEM;<host_name>;<service_description>;<sticky>;<notify>;<persistent>;<author>;<comment>
    def ACKNOWLEDGE_SVC_PROBLEM(self, service, sticky, notify, persistent, author, comment):
        service.acknowledge_problem(sticky, notify, persistent, author, comment)

    #ACKNOWLEDGE_HOST_PROBLEM;<host_name>;<sticky>;<notify>;<persistent>;<author>;<comment>
    #TODO : add a better ACK management
    def ACKNOWLEDGE_HOST_PROBLEM(self, host, sticky, notify, persistent, author, comment):
        host.acknowledge_problem(sticky, notify, persistent, author, comment)

    #CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD;<contact_name>;<notification_timeperiod>
    def CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD(self, contact, notification_timeperiod):
        contact.service_notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(contact)

    #CHANGE_CUSTOM_CONTACT_VAR;<contact_name>;<varname>;<varvalue>
    def CHANGE_CUSTOM_CONTACT_VAR(self, contact, varname, varvalue):
        contact.customs[varname.upper()] = varvalue

    #CHANGE_CUSTOM_HOST_VAR;<host_name>;<varname>;<varvalue>
    def CHANGE_CUSTOM_HOST_VAR(self, host, varname, varvalue):
        host.customs[varname.upper()] = varvalue

    #CHANGE_CUSTOM_SVC_VAR;<host_name>;<service_description>;<varname>;<varvalue>
    def CHANGE_CUSTOM_SVC_VAR(self, service, varname, varvalue):
        service.customs[varname.upper()] = varvalue

    #CHANGE_GLOBAL_HOST_EVENT_HANDLER;<event_handler_command>
    def CHANGE_GLOBAL_HOST_EVENT_HANDLER(self, event_handler_command):
        pass

    #CHANGE_GLOBAL_SVC_EVENT_HANDLER;<event_handler_command>
    def CHANGE_GLOBAL_SVC_EVENT_HANDLER(self, event_handler_command):
        pass

    #CHANGE_HOST_CHECK_COMMAND;<host_name>;<check_command>
    def CHANGE_HOST_CHECK_COMMAND(self, host, check_command):
        host.check_command = CommandCall(self.commands, check_command, poller_tag=host.poller_tag)
        self.sched.get_and_register_status_brok(host)

    #CHANGE_HOST_CHECK_TIMEPERIOD;<host_name>;<timeperiod>
    def CHANGE_HOST_CHECK_TIMEPERIOD(self, host, timeperiod):
        host.check_period = timeperiod
        self.sched.get_and_register_status_brok(service)

    #CHANGE_HOST_EVENT_HANDLER;<host_name>;<event_handler_command>
    def CHANGE_HOST_EVENT_HANDLER(self, host, event_handler_command):
        host.event_handler = CommandCall(self.commands, event_handler_command)
        self.sched.get_and_register_status_brok(host)

    #CHANGE_HOST_MODATTR;<host_name>;<value>
    def CHANGE_HOST_MODATTR(self, host, value):
        pass

    #CHANGE_MAX_HOST_CHECK_ATTEMPTS;<host_name>;<check_attempts>
    def CHANGE_MAX_HOST_CHECK_ATTEMPTS(self, host, check_attempts):
        host.max_check_attempts = check_attempts
        self.sched.get_and_register_status_brok(host)

    #CHANGE_MAX_SVC_CHECK_ATTEMPTS;<host_name>;<service_description>;<check_attempts>
    def CHANGE_MAX_SVC_CHECK_ATTEMPTS(self, service, check_attempts):
        service.max_check_attempts = check_attempts
        self.sched.get_and_register_status_brok(service)

    #CHANGE_NORMAL_HOST_CHECK_INTERVAL;<host_name>;<check_interval>
    def CHANGE_NORMAL_HOST_CHECK_INTERVAL(self, host, check_interval):
        host.check_interval = check_interval
        self.sched.get_and_register_status_brok(host)

    #CHANGE_NORMAL_SVC_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>
    def CHANGE_NORMAL_SVC_CHECK_INTERVAL(self, service, check_interval):
        service.check_interval = check_interval
        self.sched.get_and_register_status_brok(service)

    #CHANGE_RETRY_HOST_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>
    def CHANGE_RETRY_HOST_CHECK_INTERVAL(self, host, check_interval):
        host.retry_interval = check_interval
        self.sched.get_and_register_status_brok(host)

    #CHANGE_RETRY_SVC_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>
    def CHANGE_RETRY_SVC_CHECK_INTERVAL(self, service, check_interval):
        service.retry_interval = check_interval
        self.sched.get_and_register_status_brok(service)

    #CHANGE_SVC_CHECK_COMMAND;<host_name>;<service_description>;<check_command>
    def CHANGE_SVC_CHECK_COMMAND(self, service, check_command):
        service.check_command = CommandCall(self.commands, check_command, poller_tag=service.poller_tag)
        self.sched.get_and_register_status_brok(service)

    #CHANGE_SVC_CHECK_TIMEPERIOD;<host_name>;<service_description>;<check_timeperiod>
    def CHANGE_SVC_CHECK_TIMEPERIOD(self, service, check_timeperiod):
        service.check_period = check_timeperiod
        self.sched.get_and_register_status_brok(service)

    #CHANGE_SVC_EVENT_HANDLER;<host_name>;<service_description>;<event_handler_command>
    def CHANGE_SVC_EVENT_HANDLER(self, service, event_handler_command):
        service.event_handler = CommandCall(self.commands, event_handler_command)
        self.sched.get_and_register_status_brok(service)

    #CHANGE_SVC_MODATTR;<host_name>;<service_description>;<value>
    def CHANGE_SVC_MODATTR(self, service, value):
        pass

    #CHANGE_SVC_NOTIFICATION_TIMEPERIOD;<host_name>;<service_description>;<notification_timeperiod>
    def CHANGE_SVC_NOTIFICATION_TIMEPERIOD(self, service, notification_timeperiod):
        service.notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(service)

    #DELAY_HOST_NOTIFICATION;<host_name>;<notification_time>
    def DELAY_HOST_NOTIFICATION(self, host, notification_time):
        host.first_notification_delay = notification_time
        self.sched.get_and_register_status_brok(host)

    #DELAY_SVC_NOTIFICATION;<host_name>;<service_description>;<notification_time>
    def DELAY_SVC_NOTIFICATION(self, service, notification_time):
        service.first_notification_delay = notification_time
        self.sched.get_and_register_status_brok(service)

    #DEL_ALL_HOST_COMMENTS;<host_name>
    def DEL_ALL_HOST_COMMENTS(self, host):
        for c in host.comments:
            self.DEL_HOST_COMMENT(c.id)

    #DEL_ALL_SVC_COMMENTS;<host_name>;<service_description>
    def DEL_ALL_SVC_COMMENTS(self, service):
        for c in service.comments:
            self.DEL_SVC_COMMENT(c.id)

    #DEL_CONTACT_DOWNTIME;<downtime_id>
    def DEL_CONTACT_DOWNTIME(self, downtime_id):
        if downtime_id in self.sched.contact_downtimes:
            self.sched.contact_downtimes[downtime_id].cancel()


    #DEL_HOST_COMMENT;<comment_id>
    def DEL_HOST_COMMENT(self, comment_id):
        if comment_id in self.sched.comments:
            self.sched.comments[comment_id].can_be_deleted = True

    #DEL_HOST_DOWNTIME;<downtime_id>
    def DEL_HOST_DOWNTIME(self, downtime_id):
        if downtime_id in self.sched.downtimes:
            self.sched.downtimes[downtime_id].cancel()

    #DEL_SVC_COMMENT;<comment_id>
    def DEL_SVC_COMMENT(self, comment_id):
        if comment_id in self.sched.comments:
            self.sched.comments[comment_id].can_be_deleted = True

    #DEL_SVC_DOWNTIME;<downtime_id>
    def DEL_SVC_DOWNTIME(self, downtime_id):
        if downtime_id in self.sched.downtimes:
            self.sched.downtimes[downtime_id].cancel()

    #DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST;<host_name>
    def DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST(self, host):
        pass

    #DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS;<contactgroup_name>
    def DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS(self, contactgroup):
        for contact in contactgroup:
            self.DISABLE_CONTACT_HOST_NOTIFICATIONS(contact)

    #DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS;<contactgroup_name>
    def DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS(self, contactgroup):
        for contact in contactgroup:
            self.DISABLE_CONTACT_SVC_NOTIFICATIONS(contact)

    #DISABLE_CONTACT_HOST_NOTIFICATIONS;<contact_name>
    def DISABLE_CONTACT_HOST_NOTIFICATIONS(self, contact):
        contact.host_notifications_enabled = False
        self.sched.get_and_register_status_brok(contact)

    #DISABLE_CONTACT_SVC_NOTIFICATIONS;<contact_name>
    def DISABLE_CONTACT_SVC_NOTIFICATIONS(self, contact):
        contact.service_notifications_enabled = False
        self.sched.get_and_register_status_brok(contact)

    #DISABLE_EVENT_HANDLERS
    def DISABLE_EVENT_HANDLERS(self):
        self.conf.enable_event_handlers = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #DISABLE_FAILURE_PREDICTION
    def DISABLE_FAILURE_PREDICTION(self):
        self.conf.enable_failure_prediction = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #DISABLE_FLAP_DETECTION
    def DISABLE_FLAP_DETECTION(self):
        self.conf.enable_flap_detection = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #DISABLE_HOSTGROUP_HOST_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_HOST_CHECKS(self, hostgroup):
        for host in hostgroup:
            self.DISABLE_HOST_CHECK(host)

    #DISABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>
    def DISABLE_HOSTGROUP_HOST_NOTIFICATIONS(self, hostgroup):
        for host in hostgroup:
            self.DISABLE_HOST_NOTIFICATIONS(host)

    #DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS(self, hostgroup):
        for host in hostgroup:
            self.DISABLE_PASSIVE_HOST_CHECKS(host)

    #DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_PASSIVE_SVC_CHECKS(service)

    #DISABLE_HOSTGROUP_SVC_CHECKS;<hostgroup_name>
    def DISABLE_HOSTGROUP_SVC_CHECKS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_SVC_CHECK(service)

    #DISABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>
    def DISABLE_HOSTGROUP_SVC_NOTIFICATIONS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_SVC_NOTIFICATIONS(service)

    #DISABLE_HOST_AND_CHILD_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_AND_CHILD_NOTIFICATIONS(self, host):
        pass

    #DISABLE_HOST_CHECK;<host_name>
    def DISABLE_HOST_CHECK(self, host):
        host.active_checks_enabled = False
        self.sched.get_and_register_status_brok(host)

    #DISABLE_HOST_EVENT_HANDLER;<host_name>
    def DISABLE_HOST_EVENT_HANDLER(self, host):
        host.event_handler_enabled = False
        self.sched.get_and_register_status_brok(host)

    #DISABLE_HOST_FLAP_DETECTION;<host_name>
    def DISABLE_HOST_FLAP_DETECTION(self, host):
        host.flap_detection_enabled = False
        self.sched.get_and_register_status_brok(host)

    #DISABLE_HOST_FRESHNESS_CHECKS
    def DISABLE_HOST_FRESHNESS_CHECKS(self, host):
        host.check_freshness = False
        self.sched.get_and_register_status_brok(host)

    #DISABLE_HOST_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_NOTIFICATIONS(self, host):
        host.notifications_enabled = False
        self.sched.get_and_register_status_brok(host)

    #DISABLE_HOST_SVC_CHECKS;<host_name>
    def DISABLE_HOST_SVC_CHECKS(self, host):
        for s in host.services:
            self.DISABLE_SVC_CHECK(s)
            self.sched.get_and_register_status_brok(s)

    #DISABLE_HOST_SVC_NOTIFICATIONS;<host_name>
    def DISABLE_HOST_SVC_NOTIFICATIONS(self, host):
        for s in host.services:
            self.DISABLE_SVC_NOTIFICATIONS(s)
            self.sched.get_and_register_status_brok(s)

    #DISABLE_NOTIFICATIONS
    def DISABLE_NOTIFICATIONS(self):
        self.conf.enable_notifications = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #DISABLE_PASSIVE_HOST_CHECKS;<host_name>
    def DISABLE_PASSIVE_HOST_CHECKS(self, host):
        host.passive_checks_enabled = False
        self.sched.get_and_register_status_brok(host)

    #DISABLE_PASSIVE_SVC_CHECKS;<host_name>;<service_description>
    def DISABLE_PASSIVE_SVC_CHECKS(self, service):
        service.passive_checks_enabled = False
        self.sched.get_and_register_status_brok(service)

    #DISABLE_PERFORMANCE_DATA
    def DISABLE_PERFORMANCE_DATA(self):
        self.conf.process_performance_data = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #DISABLE_SERVICEGROUP_HOST_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_HOST_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_HOST_CHECK(service.host)

    #DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_HOST_NOTIFICATIONS(service.host)

    #DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_PASSIVE_HOST_CHECKS(service.host)

    #DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_PASSIVE_SVC_CHECKS(service)

    #DISABLE_SERVICEGROUP_SVC_CHECKS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_SVC_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_SVC_CHECK(service)

    #DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>
    def DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS(self, servicegroup):
        for service in servicegroup:
            self.DISABLE_SVC_NOTIFICATIONS(service)

    #DISABLE_SERVICE_FLAP_DETECTION;<host_name>;<service_description>
    def DISABLE_SERVICE_FLAP_DETECTION(self, service):
        service.flap_detection_enabled = False
        self.sched.get_and_register_status_brok(service)

    #DISABLE_SERVICE_FRESHNESS_CHECKS
    def DISABLE_SERVICE_FRESHNESS_CHECKS(self):
        self.conf.check_service_freshness = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #DISABLE_SVC_CHECK;<host_name>;<service_description>
    def DISABLE_SVC_CHECK(self, service):
        service.active_checks_enabled = False
        self.sched.get_and_register_status_brok(service)

    #DISABLE_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def DISABLE_SVC_EVENT_HANDLER(self, service):
        service.event_handler_enabled = False
        self.sched.get_and_register_status_brok(service)

    #DISABLE_SVC_FLAP_DETECTION;<host_name>;<service_description>
    def DISABLE_SVC_FLAP_DETECTION(self, service):
        service.flap_detection_enabled = False
        self.sched.get_and_register_status_brok(service)

    #DISABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>
    def DISABLE_SVC_NOTIFICATIONS(self, service):
        service.notifications_enabled = False
        self.sched.get_and_register_status_brok(service)

    #ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST;<host_name>
    def ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST(self, host):
        pass

    #ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS;<contactgroup_name>
    def ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS(self, contactgroup):
        for contact in contactgroup:
            self.ENABLE_CONTACT_HOST_NOTIFICATIONS(contact)

    #ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS;<contactgroup_name>
    def ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS(self, contactgroup):
        for contact in contactgroup:
            self.ENABLE_CONTACT_SVC_NOTIFICATIONS(contact)

    #ENABLE_CONTACT_HOST_NOTIFICATIONS;<contact_name>
    def ENABLE_CONTACT_HOST_NOTIFICATIONS(self, contact):
        contact.host_notifications_enabled = True
        self.sched.get_and_register_status_brok(contact)

    #ENABLE_CONTACT_SVC_NOTIFICATIONS;<contact_name>
    def ENABLE_CONTACT_SVC_NOTIFICATIONS(self, contact):
        contact.service_notifications_enabled = True
        self.sched.get_and_register_status_brok(contact)

    #ENABLE_EVENT_HANDLERS
    def ENABLE_EVENT_HANDLERS(self):
        self.conf.enable_event_handlers = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #ENABLE_FAILURE_PREDICTION
    def ENABLE_FAILURE_PREDICTION(self):
        self.conf.enable_failure_prediction = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #ENABLE_FLAP_DETECTION
    def ENABLE_FLAP_DETECTION(self):
        self.conf.enable_flap_detection = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #ENABLE_HOSTGROUP_HOST_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_HOST_CHECKS(self, hostgroup):
        for host in hostgroup:
            self.ENABLE_HOST_CHECK(host)

    #ENABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>
    def ENABLE_HOSTGROUP_HOST_NOTIFICATIONS(self, hostgroup):
        for host in hostgroup:
            self.ENABLE_HOST_NOTIFICATIONS(host)

    #ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS(self, hostgroup):
        for host in hostgroup:
            self.ENABLE_PASSIVE_HOST_CHECKS(host)

    #ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_PASSIVE_SVC_CHECKS(service)

    #ENABLE_HOSTGROUP_SVC_CHECKS;<hostgroup_name>
    def ENABLE_HOSTGROUP_SVC_CHECKS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_SVC_CHECK(service)

    #ENABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>
    def ENABLE_HOSTGROUP_SVC_NOTIFICATIONS(self, hostgroup):
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_SVC_NOTIFICATIONS(service)

    #ENABLE_HOST_AND_CHILD_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_AND_CHILD_NOTIFICATIONS(self, host):
        pass

    #ENABLE_HOST_CHECK;<host_name>
    def ENABLE_HOST_CHECK(self, host):
        host.active_checks_enabled = True
        self.sched.get_and_register_status_brok(host)

    #ENABLE_HOST_EVENT_HANDLER;<host_name>
    def ENABLE_HOST_EVENT_HANDLER(self, host):
        host.enable_event_handlers = True
        self.sched.get_and_register_status_brok(host)

    #ENABLE_HOST_FLAP_DETECTION;<host_name>
    def ENABLE_HOST_FLAP_DETECTION(self, host):
        host.flap_detection_enabled = True
        self.sched.get_and_register_status_brok(host)

    #ENABLE_HOST_FRESHNESS_CHECKS
    def ENABLE_HOST_FRESHNESS_CHECKS(self):
        self.conf.check_host_freshness = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #ENABLE_HOST_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_NOTIFICATIONS(self, host):
        host.notifications_enabled = True
        self.sched.get_and_register_status_brok(host)

    #ENABLE_HOST_SVC_CHECKS;<host_name>
    def ENABLE_HOST_SVC_CHECKS(self, host):
        for s in host.services:
            self.ENABLE_SVC_CHECK(s)
            self.sched.get_and_register_status_brok(s)

    #ENABLE_HOST_SVC_NOTIFICATIONS;<host_name>
    def ENABLE_HOST_SVC_NOTIFICATIONS(self, host):
        for s in host.services:
            self.ENABLE_SVC_NOTIFICATIONS(s)
            self.sched.get_and_register_status_brok(s)

    #ENABLE_NOTIFICATIONS
    def ENABLE_NOTIFICATIONS(self):
        self.conf.enable_notifications = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #ENABLE_PASSIVE_HOST_CHECKS;<host_name>
    def ENABLE_PASSIVE_HOST_CHECKS(self, host):
        host.passive_checks_enabled = True
        self.sched.get_and_register_status_brok(host)

    #ENABLE_PASSIVE_SVC_CHECKS;<host_name>;<service_description>
    def ENABLE_PASSIVE_SVC_CHECKS(self, service):
        service.passive_checks_enabled = True
        self.sched.get_and_register_status_brok(service)

    #ENABLE_PERFORMANCE_DATA
    def ENABLE_PERFORMANCE_DATA(self):
        self.conf.process_performance_data = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #ENABLE_SERVICEGROUP_HOST_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_HOST_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_HOST_CHECK(service.host)

    #ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_HOST_NOTIFICATIONS(service.host)

    #ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_PASSIVE_HOST_CHECKS(service.host)

    #ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_PASSIVE_SVC_CHECKS(service)

    #ENABLE_SERVICEGROUP_SVC_CHECKS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_SVC_CHECKS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_SVC_CHECK(service)

    #ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>
    def ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS(self, servicegroup):
        for service in servicegroup:
            self.ENABLE_SVC_NOTIFICATIONS(service)

    #ENABLE_SERVICE_FRESHNESS_CHECKS
    def ENABLE_SERVICE_FRESHNESS_CHECKS(self):
        self.conf.check_service_freshness = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #ENABLE_SVC_CHECK;<host_name>;<service_description>
    def ENABLE_SVC_CHECK(self, service):
        service.active_checks_enabled = True
        self.sched.get_and_register_status_brok(service)

    #ENABLE_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def ENABLE_SVC_EVENT_HANDLER(self, service):
        service.event_handler_enabled = True
        self.sched.get_and_register_status_brok(service)

    #ENABLE_SVC_FLAP_DETECTION;<host_name>;<service_description>
    def ENABLE_SVC_FLAP_DETECTION(self, service):
        service.flap_detection_enabled = True
        self.sched.get_and_register_status_brok(service)

    #ENABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>
    def ENABLE_SVC_NOTIFICATIONS(self, service):
        service.notifications_enabled = True
        self.sched.get_and_register_status_brok(service)

    #PROCESS_FILE;<file_name>;<delete>
    def PROCESS_FILE(self, file_name, delete):
        pass

    #TODO : say that check is PASSIVE
    #PROCESS_HOST_CHECK_RESULT;<host_name>;<status_code>;<plugin_output>
    def PROCESS_HOST_CHECK_RESULT(self, host, status_code, plugin_output):
        #raise a PASSIVE check only if needed
        if self.conf.log_passive_checks:
            logger.log('PASSIVE HOST CHECK: %s;%d;%s' % (host.get_name(), status_code, plugin_output))
        now = time.time()
        cls = host.__class__
        #If globally disable OR locally, do not launch
        if cls.accept_passive_checks and host.passive_checks_enabled:
            i = host.launch_check(now, force=True)
            for chk in host.actions:
                if chk.id == i:
                    c = chk
            #Now we 'transform the check into a result'
            #So exit_status, output and status is eaten by the host
            c.exit_status = status_code
            c.get_outputs(plugin_output, host.max_plugins_output_length)
            c.status = 'waitconsume'
            c.check_time = now
            self.sched.nb_check_received += 1
            #Ok now this result will be reap by scheduler the next loop


    #PROCESS_SERVICE_CHECK_RESULT;<host_name>;<service_description>;<return_code>;<plugin_output>
    def PROCESS_SERVICE_CHECK_RESULT(self, service, return_code, plugin_output):
        #raise a PASSIVE check only if needed
        if self.conf.log_passive_checks:
            logger.log('PASSIVE SERVICE CHECK: %s;%s;%d;%s' % (service.host.get_name(), service.get_name(), return_code, plugin_output))
        now = time.time()
        cls = service.__class__
        #If globally disable OR locally, do not launch
        if cls.accept_passive_checks and service.passive_checks_enabled:
            i = service.launch_check(now, force=True)
            for chk in service.actions:
                if chk.id == i:
                    c = chk
            #Now we 'transform the check into a result'
            #So exit_status, output and status is eaten by the service
            c.exit_status = return_code
            c.get_outputs(plugin_output, service.max_plugins_output_length)
            c.status = 'waitconsume'
            c.check_time = now
            self.sched.nb_check_received += 1
            #Ok now this result will be reap by scheduler the next loop


    #READ_STATE_INFORMATION
    def READ_STATE_INFORMATION(self):
        pass

    #REMOVE_HOST_ACKNOWLEDGEMENT;<host_name>
    def REMOVE_HOST_ACKNOWLEDGEMENT(self, host):
        host.unacknowledge_problem()

    #REMOVE_SVC_ACKNOWLEDGEMENT;<host_name>;<service_description>
    def REMOVE_SVC_ACKNOWLEDGEMENT(self, service):
        service.unacknowledge_problem()

    #RESTART_PROGRAM
    def RESTART_PROGRAM(self):
        pass

    #SAVE_STATE_INFORMATION
    def SAVE_STATE_INFORMATION(self):
        pass

    #SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME(self, host, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME(self, host, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_CONTACT_DOWNTIME;<contact_name>;<start_time>;<end_time>;<author>;<comment>
    def SCHEDULE_CONTACT_DOWNTIME(self, contact, start_time, end_time, author, comment):
        dt = ContactDowntime(contact, start_time, end_time, author, comment)
        contact.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(contact)

    #SCHEDULE_FORCED_HOST_CHECK;<host_name>;<check_time>
    def SCHEDULE_FORCED_HOST_CHECK(self, host, check_time):
        host.schedule(force=True, force_time=check_time)
        self.sched.get_and_register_status_brok(host)

    #SCHEDULE_FORCED_HOST_SVC_CHECKS;<host_name>;<check_time>
    def SCHEDULE_FORCED_HOST_SVC_CHECKS(self, host, check_time):
        for s in host.services:
            self.SCHEDULE_FORCED_SVC_CHECK(s, check_time)
            self.sched.get_and_register_status_brok(s)

    #SCHEDULE_FORCED_SVC_CHECK;<host_name>;<service_description>;<check_time>
    def SCHEDULE_FORCED_SVC_CHECK(self, service, check_time):
        service.schedule(force=True, force_time=check_time)
        self.sched.get_and_register_status_brok(service)

    #SCHEDULE_HOSTGROUP_HOST_DOWNTIME;<hostgroup_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOSTGROUP_HOST_DOWNTIME(self, hostgroup, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_HOSTGROUP_SVC_DOWNTIME;<hostgroup_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOSTGROUP_SVC_DOWNTIME(self, hostgroup, start_time, end_time, fixed, trigger_id, duration, author, comment):
        pass

    #SCHEDULE_HOST_CHECK;<host_name>;<check_time>
    def SCHEDULE_HOST_CHECK(self, host, check_time):
        host.schedule(force=False, force_time=check_time)
        self.sched.get_and_register_status_brok(host)

    #SCHEDULE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOST_DOWNTIME(self, host, start_time, end_time, fixed, trigger_id, duration, author, comment):
        dt = Downtime(host, start_time, end_time, fixed, trigger_id, duration, author, comment)
        host.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(host)
        if trigger_id != 0 and trigger_id in self.sched.downtimes:
            self.sched.downtimes[trigger_id].trigger_me(dt)

    #SCHEDULE_HOST_SVC_CHECKS;<host_name>;<check_time>
    def SCHEDULE_HOST_SVC_CHECKS(self, host, check_time):
        for s in host.services:
            self.SCHEDULE_SVC_CHECK(s, check_time)
            self.sched.get_and_register_status_brok(s)

    #SCHEDULE_HOST_SVC_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_HOST_SVC_DOWNTIME(self, host, start_time, end_time, fixed, trigger_id, duration, author, comment):
        for s in host.services:
            self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed, trigger_id, duration, author, comment)

    #SCHEDULE_SERVICEGROUP_HOST_DOWNTIME;<servicegroup_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SERVICEGROUP_HOST_DOWNTIME(self, servicegroup, start_time, end_time, fixed, trigger_id, duration, author, comment):
        for h in [s.host for s in servicegroup.get_services()]:
            self.SCHEDULE_HOST_DOWNTIME(h, start_time, end_time, fixed, trigger_id, duration, author, comment)

    #SCHEDULE_SERVICEGROUP_SVC_DOWNTIME;<servicegroup_name>;<start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SERVICEGROUP_SVC_DOWNTIME(self, servicegroup, start_time, end_time, fixed, trigger_id, duration, author, comment):
        for s in servicegroup.get_services():
            self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed, trigger_id, duration, author, comment)

    #SCHEDULE_SVC_CHECK;<host_name>;<service_description>;<check_time>
    def SCHEDULE_SVC_CHECK(self, service, check_time):
        service.schedule(force=False, force_time=check_time)
        self.sched.get_and_register_status_brok(service)

    #SCHEDULE_SVC_DOWNTIME;<host_name>;<service_desription><start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
    def SCHEDULE_SVC_DOWNTIME(self, service, start_time, end_time, fixed, trigger_id, duration, author, comment):
        dt = Downtime(service, start_time, end_time, fixed, trigger_id, duration, author, comment)
        service.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(service)
        if trigger_id != 0 and trigger_id in self.sched.downtimes:
            self.sched.downtimes[trigger_id].trigger_me(dt)

    #SEND_CUSTOM_HOST_NOTIFICATION;<host_name>;<options>;<author>;<comment>
    def SEND_CUSTOM_HOST_NOTIFICATION(self, host, options, author, comment):
        pass

    #SEND_CUSTOM_SVC_NOTIFICATION;<host_name>;<service_description>;<options>;<author>;<comment>
    def SEND_CUSTOM_SVC_NOTIFICATION(self, service, options, author, comment):
        pass

    #SET_HOST_NOTIFICATION_NUMBER;<host_name>;<notification_number>
    def SET_HOST_NOTIFICATION_NUMBER(self, host, notification_number):
        pass

    #SET_SVC_NOTIFICATION_NUMBER;<host_name>;<service_description>;<notification_number>
    def SET_SVC_NOTIFICATION_NUMBER(self, service, notification_number):
        pass

    #SHUTDOWN_PROGRAM
    def SHUTDOWN_PROGRAM(self):
        pass

    #START_ACCEPTING_PASSIVE_HOST_CHECKS
    def START_ACCEPTING_PASSIVE_HOST_CHECKS(self):
        self.conf.accept_passive_host_checks = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #START_ACCEPTING_PASSIVE_SVC_CHECKS
    def START_ACCEPTING_PASSIVE_SVC_CHECKS(self):
        self.conf.accept_passive_service_checks = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #START_EXECUTING_HOST_CHECKS
    def START_EXECUTING_HOST_CHECKS(self):
        self.conf.execute_host_checks = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #START_EXECUTING_SVC_CHECKS
    def START_EXECUTING_SVC_CHECKS(self):
        self.conf.execute_service_checks = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #START_OBSESSING_OVER_HOST;<host_name>
    def START_OBSESSING_OVER_HOST(self, host):
        host.obsess_over_host = True
        self.sched.get_and_register_status_brok(host)

    #START_OBSESSING_OVER_HOST_CHECKS
    def START_OBSESSING_OVER_HOST_CHECKS(self):
        self.conf.obsess_over_hosts = True
        self.conf.explode_global_conf()

    #START_OBSESSING_OVER_SVC;<host_name>;<service_description>
    def START_OBSESSING_OVER_SVC(self, service):
        service.obsess_over_service = True
        self.sched.get_and_register_status_brok(service)

    #START_OBSESSING_OVER_SVC_CHECKS
    def START_OBSESSING_OVER_SVC_CHECKS(self):
        self.conf.obsess_over_services = True
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #STOP_ACCEPTING_PASSIVE_HOST_CHECKS
    def STOP_ACCEPTING_PASSIVE_HOST_CHECKS(self):
        self.accept_passive_host_checks = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #STOP_ACCEPTING_PASSIVE_SVC_CHECKS
    def STOP_ACCEPTING_PASSIVE_SVC_CHECKS(self):
        self.accept_passive_service_checks = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #STOP_EXECUTING_HOST_CHECKS
    def STOP_EXECUTING_HOST_CHECKS(self):
        self.conf.execute_host_checks = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #STOP_EXECUTING_SVC_CHECKS
    def STOP_EXECUTING_SVC_CHECKS(self):
        self.conf.execute_service_checks = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #STOP_OBSESSING_OVER_HOST;<host_name>
    def STOP_OBSESSING_OVER_HOST(self, host):
        host.obsess_over_host = False
        self.sched.get_and_register_status_brok(host)

    #STOP_OBSESSING_OVER_HOST_CHECKS
    def STOP_OBSESSING_OVER_HOST_CHECKS(self):
        self.conf.obsess_over_hosts = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()

    #STOP_OBSESSING_OVER_SVC;<host_name>;<service_description>
    def STOP_OBSESSING_OVER_SVC(self, service):
        service.obsess_over_service = False
        self.sched.get_and_register_status_brok(service)

    #STOP_OBSESSING_OVER_SVC_CHECKS
    def STOP_OBSESSING_OVER_SVC_CHECKS(self):
        self.conf.obsess_over_services = False
        self.conf.explode_global_conf()
        self.sched.get_and_register_update_program_status_brok()


    ### Now the shinken specific ones
    #LAUNCH_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def LAUNCH_SVC_EVENT_HANDLER(self, service):
        service.get_event_handlers(externalcmd=True)


    #LAUNCH_SVC_EVENT_HANDLER;<host_name>;<service_description>
    def LAUNCH_HOST_EVENT_HANDLER(self, host):
        host.get_event_handlers(externalcmd=True)


    #ADD_SIMPLE_HOST_DEPENDENCY;<host_name>;<host_name>
    def ADD_SIMPLE_HOST_DEPENDENCY(self, son, father):
        if not son.is_linked_with_host(father):
            print "Doing simple link between", son.get_name(), 'and', father.get_name()
            # Add a dep link between the son and the father
            son.add_host_act_dependancy(father, ['w', 'u', 'd'], None, True)
            self.sched.get_and_register_status_brok(son)
            self.sched.get_and_register_status_brok(father)
        

    #ADD_SIMPLE_HOST_DEPENDENCY;<host_name>;<host_name>
    def DEL_HOST_DEPENDENCY(self, son, father):
        if son.is_linked_with_host(father):
            print "removing simple link between", son.get_name(), 'and', father.get_name()
            son.del_host_act_dependancy(father)
            self.sched.get_and_register_status_brok(son)
            self.sched.get_and_register_status_brok(father)


    #ADD_SIMPLE_POLLER;realm_name;poller_name;address;port
    def ADD_SIMPLE_POLLER(self, realm_name, poller_name, address, port):
        print "I need to add the poller", realm_name, poller_name, address, port

        # First we look for the realm
        r = self.conf.realms.find_by_name(realm_name)
        if r is None:
            print "Sorry, the realm %s is unknown" % realm_name
            return
        print "We found the realm", r
        # TODO : backport this in the config class?
        # We create the PollerLink object
        t = {'poller_name' : poller_name, 'address' : address, 'port' : port}
        p = PollerLink(t)
        p.fill_default()
        p.pythonize()
        p.prepare_for_conf()
        parameters = {'max_plugins_output_length' : self.conf.max_plugins_output_length}
        p.add_global_conf_parameters(parameters)
        self.arbiter.conf.pollers[p.id] = p
        self.arbiter.dispatcher.elements.append(p)
        self.arbiter.dispatcher.satellites.append(p)
        r.pollers.append(p)
        r.count_pollers()
        r.fill_potential_pollers()
        print "Poller %s added" % poller_name
        print "Potential", r.get_potential_satellites_by_type('poller')


if __name__ == '__main__':

    FIFO_PATH = '/tmp/my_fifo'

    if os.path.exists(FIFO_PATH):
        os.unlink(FIFO_PATH)

    if not os.path.exists(FIFO_PATH):
        os.umask(0)
        os.mkfifo(FIFO_PATH, 0660)
        my_fifo = open(FIFO_PATH, 'w+')
        print "my_fifo:", my_fifo

    print open(FIFO_PATH, 'r').readline()
