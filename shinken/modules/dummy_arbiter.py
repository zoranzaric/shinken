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


#This Class is an example of an Arbiter module
#Here for the configuration phase AND running one


#This text is print at the import
print "Detected module : Dummy module for Arbiter"


import time


from shinken.basemodule import BaseModule

from shinken.external_command import ExternalCommand


properties = {
    'type' : 'dummy_arbiter',
    'external' : True,
    'phases' : ['configuration', 'late_configuration', 'running'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Dummy arbiter module for plugin %s" % plugin.get_name()
    instance = Dummy_arbiter(plugin)
    return instance



#Just print some stuff
class Dummy_arbiter(BaseModule):
    if False:  ## useless to define this:
        def __init__(self, mod_conf):
            BaseModule.__init__(mod_conf)

    #Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the dummy arbiter module"
        #self.return_queue = self.properties['from_queue']
        

    #Ok, main function that is called in the CONFIGURATION phase
    def get_objects(self):
        print "[Dummy] ask me for objects to return"
        r = {'hosts' : []}
        h = {'name' : 'dummy host from dummy arbiter module',
             'register' : '0',
             }
        
        r['hosts'].append(h)
        r['hosts'].append( {
                            'host_name': "dummyhost1",
                            'use': 'linux-server',
                            'address': 'localhost'
                            })
        print "[Dummy] Returning to Arbiter the hosts:", r
        return r
    
    def hook_late_configuration(self, conf):
        print("Dummy in hook late config")

    def do_loop_turn(self):
        print "Raise a external command as example"
        e = ExternalCommand('Viva la revolution')
        self.from_q.put(e)
        time.sleep(1)

