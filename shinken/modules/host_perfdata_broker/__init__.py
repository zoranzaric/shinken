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


#This text is print at the import
print "I am Host Perfdata Broker"


properties = {
    'daemons' : ['broker'],
    'type' : 'host_perfdata',
    'phases' : ['running'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Host Perfdata broker for plugin %s" % plugin.get_name()

    #First try to import
    try:
        from host_perfdata_broker import Host_perfdata_broker
    except ImportError , exp:
        print "Warning : the plugin type %s is unavailable : %s" % (get_type(), exp)
        return None


    #Catch errors
    path = plugin.path
    if hasattr(plugin, 'mode'):
        mode = plugin.mode
    else:
        mode = 'a'

    if hasattr(plugin, 'template'):
        template = plugin.template
    else:
        template = "$LASTHOSTCHECK$\t$HOSTNAME$\t$HOSTOUTPUT$\t$HOSTSTATE$\t$HOSTPERFDATA$\n"
        # int(data['last_chk']),data['host_name'], data['service_description'], data['output'], current_state, data['perf_data']

    instance = Host_perfdata_broker(plugin, path, mode, template)
    return instance
