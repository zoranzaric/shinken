#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


#This Class is a plugin for the Shinken Broker. It is in charge
#to brok information of the service perfdata into the file
#var/service-perfdata
#So it just manage the service_check_return
#Maybe one day host data will be usefull too
#It will need just a new file, and a new manager :)


from shinken.basemodule import BaseModule

#Class for the Merlindb Broker
#Get broks and puts them in merlin database
class Host_perfdata_broker(BaseModule):
    def __init__(self, modconf, path, mode, template):
        BaseModule.__init__(self, modconf)
        self.path = path
        self.mode = mode
        self.template = template

        #Make some raw change
        self.template = self.template.replace(r'\t', '\t')
        self.template = self.template.replace(r'\n', '\n')


    #Called by Broker so we can do init stuff
    #TODO : add conf param to get pass with init
    #Conf from arbiter!
    def init(self):
        print "I open the host-perfdata file '%s'" % self.path
        self.file = open(self.path, self.mode)


    #We've got a 0, 1, 2 or 3 (or something else? ->3
    #And want a real OK, WARNING, CRITICAL, etc...
    def resolve_host_state(self, state):
        states = {0 : 'UP', 1 : 'DOWN', 2 : 'DOWN', 3 : 'UNKNOWN'}
        if state in states:
            return states[state]
        else:
            return 'UNKNOWN'


    #A service check have just arrived, we UPDATE data info with this
    def manage_host_check_result_brok(self, b):
        data = b.data
        #The original model
        #"$TIMET\t$HOSTNAME\t$OUTPUT\t$SERVICESTATE\t$PERFDATA\n"
        current_state = self.resolve_host_state(data['state_id'])
        macros = {
            '$LASTHOSTCHECK$' : int(data['last_chk']),
            '$HOSTNAME$' : data['host_name'],
            '$HOSTOUTPUT$' : data['output'],
            '$HOSTSTATE$' : current_state,
            '$HOSTPERFDATA$' : data['perf_data'],
            }
        s = self.template
        for m in macros:
            s = s.replace(m, str(macros[m]))
        #s = "%s\t%s\t%s\t%s\t%s\n" % (int(data['last_chk']),data['host_name'], \
        #                                  data['output'], \
        #                                  current_state, data['perf_data'] )
        self.file.write(s)
        self.file.flush()
