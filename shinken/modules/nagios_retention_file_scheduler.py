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


#This Class is an example of an Scheduler module
#Here for the configuration phase AND running one


import re, string

from shinken.config import Config
from shinken.timeperiod import Timeperiod, Timeperiods
from shinken.service import Service, Services
from shinken.command import Command, Commands
from shinken.resultmodulation import Resultmodulation, Resultmodulations
from shinken.escalation import Escalation, Escalations
from shinken.serviceescalation import Serviceescalation, Serviceescalations
from shinken.hostescalation import Hostescalation, Hostescalations
from shinken.host import Host, Hosts
from shinken.hostgroup import Hostgroup, Hostgroups
from shinken.realm import Realm, Realms
from shinken.contact import Contact, Contacts
from shinken.contactgroup import Contactgroup, Contactgroups
from shinken.notificationway import NotificationWay, NotificationWays
from shinken.servicegroup import Servicegroup, Servicegroups
from shinken.item import Item
from shinken.servicedependency import Servicedependency, Servicedependencies
from shinken.hostdependency import Hostdependency, Hostdependencies
from shinken.arbiterlink import ArbiterLink, ArbiterLinks
from shinken.schedulerlink import SchedulerLink, SchedulerLinks
from shinken.reactionnerlink import ReactionnerLink, ReactionnerLinks
from shinken.brokerlink import BrokerLink, BrokerLinks
from shinken.pollerlink import PollerLink, PollerLinks
from shinken.module import Module, Modules
from shinken.graph import Graph
from shinken.log import logger
from shinken.comment import Comment
from shinken.downtime import Downtime

from shinken.util import to_int, to_char, to_bool



#This text is print at the import
print "Detected module : Nagios retention file for Scheduler (load only!)"


properties = {
    'type' : 'nagios_retention_file',
    'external' : False,
    'phases' : ['retention'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Nagios3 retention scheduler module for plugin %s" % plugin.get_name()
    path = plugin.path
    instance = Nagios_retention_scheduler(plugin.get_name(), path)
    return instance



#Just print some stuff
class Nagios_retention_scheduler:
    def __init__(self, name, path):
        self.name = name
        self.path = path

    #Called by Scheduler to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the Nagios file retention scheduler module"
        #self.return_queue = self.properties['from_queue']


    def get_name(self):
        return self.name


    #Ok, main function that is called in the retention creation pass
    def update_retention_objects(self, sched, log_mgr):
        print "[NagiosRetention] asking me to update the retention objects, but I won't do it."



    def _cut_line(self, line):
        #punct = '"#$%&\'()*+/<=>?@[\\]^`{|}~'
        tmp = re.split("=", line)
        r = [elt for elt in tmp if elt != '']
        return r


    def read_retention_buf(self, buf):
        params = []
        objectscfg = {'void': [],
                      'timeperiod' : [],
                      'command' : [],
                      'contactgroup' : [],
                      'hostgroup' : [],
                      'contact' : [],
                      'notificationway' : [],
                      'host' : [],
                      'service' : [],
                      'servicegroup' : [],
                      'servicedependency' : [],
                      'hostdependency' : [],
                      'hostcomment' : [],
                      'hostdowntime' : [],
                      'servicecomment' : [],
                      'servicedowntime' : [],
                      }
        tmp = []
        tmp_type = 'void'
        in_define = False
        continuation_line = False
        tmp_line = ''
        lines = buf.split('\n')
        for line in lines:
            line = line.split(';')[0]
            #A backslash means, there is more to come
            if re.search("\\\s*$", line):
                continuation_line = True
                line = re.sub("\\\s*$", "", line)
                line = re.sub("^\s+", " ", line)
                tmp_line += line
                continue
            elif continuation_line:
                #Now the continuation line is complete
                line = re.sub("^\s+", "", line)
                line = tmp_line + line
                tmp_line = ''
                continuation_line = False
            if re.search("}", line):
                in_define = False
            if re.search("^\s*\t*#|^\s*$|^\s*}", line):
                pass

            #A define must be catch and the type save
            #The old entry must be save before
            elif re.search("{$", line):
                in_define = True
                if tmp_type not in objectscfg:
                    objectscfg[tmp_type] = []
                objectscfg[tmp_type].append(tmp)
                tmp = []
                #Get new type
                elts = re.split('\s', line)
                tmp_type = elts[0]
#                tmp_type = tmp_type.split('{')[0]
#                print "TMP type", tmp_type
            else:
                if in_define:
                    tmp.append(line)
                else:
                    params.append(line)

        objectscfg[tmp_type].append(tmp)
        objects = {}

#        print "Loaded", objectscfg

        for type in objectscfg:
            objects[type] = []
            for items in objectscfg[type]:
                tmp = {}
                for line in items:
                    elts = self._cut_line(line)
                    if elts !=  []:
                        prop = elts[0]
                        value = ' '.join(elts[1:])
                        tmp[prop] = value
                if tmp != {}:
                    objects[type].append(tmp)

        return objects


    #We've got raw objects in string, now create real Instances
    def create_objects(self, raw_objects, types_creations):
        all_obj = {}
        for t in types_creations:
            all_obj[t] = self.create_objects_for_type(raw_objects, t, types_creations)
        return all_obj


    def pythonize_running(self, obj, obj_cfg):
        cls = obj.__class__
        running_properties = cls.running_properties
        for prop in running_properties:
            entry = running_properties[prop]
            if hasattr(obj, prop) and prop in obj_cfg:
                if 'pythonize' in entry:
                    f = entry['pythonize']
                    if f != None: # mean it's a string
                        #print "Apply", f, "to the property", prop, "for ", cls.my_type
                        val = getattr(obj, prop)
                        val = f(val)
                        setattr(obj, prop, val)
                else: #no pythonize, int by default
                    # if cls.my_type != 'service':
                    #  print "Intify", prop, getattr(obj, prop)
                    if prop != 'state_type':
                        val = int(getattr(obj, prop))
                        setattr(obj, prop, val)
                    else:#state type is a int, but should be set HARd or SOFT
                        val = int(getattr(obj, prop))
                        if val == 1:
                            setattr(obj, prop, 'HARD')
                        else:
                            setattr(obj, prop, 'SOFT')


                    
    def create_objects_for_type(self, raw_objects, type, types_creations):
        t = type
        #Ex: the above code do for timeperiods:
        #timeperiods = []
        #for timeperiodcfg in objects['timeperiod']:
        #    t = Timeperiod(timeperiodcfg)
        #    t.clean()
        #    timeperiods.append(t)
        #self.timeperiods = Timeperiods(timeperiods)

        (cls, clss, prop) = types_creations[t]
        #List where we put objects
        lst = []
        for obj_cfg in raw_objects[t]:
            #We create teh object
            #print "Create obj", obj_cfg
            o = cls(obj_cfg)
            o.clean()
            if t in self.property_mapping:
                entry = self.property_mapping[t]
                for (old, new) in entry:
                    value = getattr(o, old)
                    setattr(o, new, value)
                    delattr(o, old)
                    obj_cfg[new] = obj_cfg[old]
                    del obj_cfg[old]
            o.pythonize()
            self.pythonize_running(o, obj_cfg)
            lst.append(o)
        #print "Got", lst
        #we create the objects Class and we set it in prop
        #setattr(self, prop, clss(lst))
        #print "Object?", clss(lst)
        return clss(lst)


    def create_and_link_comments(self, raw_objects, all_obj):
    #first service
        for obj_cfg in raw_objects['servicecomment']:
        #print "Managing", obj_cfg
            host_name = obj_cfg['host_name']
            service_description = obj_cfg['service_description']
            srv = all_obj['service'].find_srv_by_name_and_hostname(host_name, service_description)
        #print "Find my service", srv
            if srv != None:
                cmd = Comment(srv, to_bool(obj_cfg['persistent']), obj_cfg['author'], obj_cfg['comment_data'], 1, int(obj_cfg['entry_type']), int(obj_cfg['source']), to_bool(obj_cfg['expires']), int(obj_cfg['expire_time']))
            #print "Created cmd", cmd
                srv.add_comment(cmd)

    #then hosts
        for obj_cfg in raw_objects['hostcomment']:
        #print "Managing", obj_cfg
            host_name = obj_cfg['host_name']
            hst = all_obj['host'].find_by_name(host_name)
        #print "Find my host", hst
            if hst != None:
                cmd = Comment(hst, to_bool(obj_cfg['persistent']), obj_cfg['author'], obj_cfg['comment_data'], 1, int(obj_cfg['entry_type']), int(obj_cfg['source']), to_bool(obj_cfg['expires']), int(obj_cfg['expire_time']))
            #print "Created cmd", cmd
                hst.add_comment(cmd)




    def create_and_link_downtimes(self, raw_objects, all_obj):
    #first service
        for obj_cfg in raw_objects['servicedowntime']:
            print "Managing", obj_cfg
            host_name = obj_cfg['host_name']
            service_description = obj_cfg['service_description']
            srv = all_obj['service'].find_srv_by_name_and_hostname(host_name, service_description)
            print "Find my service", srv
            if srv != None:
                dwn = Downtime(srv, int(obj_cfg['start_time']), int(obj_cfg['end_time']), to_bool(obj_cfg['fixed']), int(obj_cfg['triggered_by']), int(obj_cfg['duration']), obj_cfg['author'], obj_cfg['comment'])
                print "Created dwn", dwn
                srv.add_downtime(dwn)

    #then hosts
        for obj_cfg in raw_objects['hostdowntime']:
            print "Managing", obj_cfg
            host_name = obj_cfg['host_name']
            hst = all_obj['host'].find_by_name(host_name)
            print "Find my host", hst
            if hst != None:
                dwn = Downtime(hst, int(obj_cfg['start_time']), int(obj_cfg['end_time']), to_bool(obj_cfg['fixed']), int(obj_cfg['triggered_by']), int(obj_cfg['duration']), obj_cfg['author'], obj_cfg['comment'])
                print "Created dwn", dwn
                hst.add_downtime(dwn)



    #Should return if it succeed in the retention load or not
    def load_retention_objects(self, sched, log_mgr):
        print "[NagiosRetention] asking me to load the retention file"

        #Now the old flat file way :(
        log_mgr.log("[NagiosRetention]Reading from retention_file %s" % self.path)
        try:
            f = open(self.path)
            buf = f.read()
            f.close()
        except EOFError , exp:
            print exp
            return False
        except ValueError , exp:
            print exp
            return False
        except IOError , exp:
            print exp
            return False
        except IndexError , exp:
            s = "WARNING: Sorry, the ressource file is not compatible"
            log_mgr.log(s)
            return False
        except TypeError , exp:
            s = "WARNING: Sorry, the ressource file is not compatible"
            log_mgr.log(s)
            return False


        print "Fin read config"
        raw_objects = self.read_retention_buf(buf)
        print "Fun raw"
        
        types_creations = {'timeperiod' : (Timeperiod, Timeperiods, 'timeperiods'),
                   'service' : (Service, Services, 'services'),
                   'host' : (Host, Hosts, 'hosts'),
                   'contact' : (Contact, Contacts, 'contacts'),
                   }


        self.property_mapping = {
            'service' : [('current_attempt', 'attempt'), ('current_state','state_type_id'),
                         ('plugin_output','output'), ('last_check','last_chk'),
                         ('performance_data','perf_data'), ('next_check' , 'next_chk'),
                         ('long_plugin_output', 'long_output'), ('check_execution_time', 'execution_time'),
                         ('check_latency', 'latency')],
            'host' : [('current_attempt', 'attempt'), ('current_state','state_type_id'),
                      ('plugin_output','output'), ('last_check','last_chk'),
                 ('performance_data','perf_data'), ('next_check' , 'next_chk'),
                      ('long_plugin_output', 'long_output'), ('check_execution_time', 'execution_time'),
                      ('check_latency', 'latency')],
            }

        all_obj = self.create_objects(raw_objects, types_creations)


        print "Got all obj", all_obj

        self.create_and_link_comments(raw_objects, all_obj)

        self.create_and_link_downtimes(raw_objects, all_obj)

        #Now load interesting properties in hosts/services
        #Taging retention=False prop that not be directly load
        #Items will be with theirs status, but not in checking, so
        #a new check will be launch like with a normal begining (random distributed
        #scheduling)

        ret_hosts = all_obj['host']
        for ret_h in ret_hosts:
            h = sched.hosts.find_by_name(ret_h.host_name)
            if h != None:
#                print "Ok, got data for", h.get_dbg_name()
                running_properties = h.__class__.running_properties
                for prop in running_properties:
                    entry = running_properties[prop]
                    if 'retention' in entry and entry['retention']:
#                        print "Set host value", getattr(ret_h, prop)
                        setattr(h, prop, getattr(ret_h, prop))
                for a in h.notifications_in_progress.values():
                    a.ref = h
                    sched.add(a)
                h.update_in_checking()
                #And also add downtimes and comments
                for dt in h.downtimes:
                    dt.ref = h
                    sched.add(dt)
                for c in h.comments:
                    c.ref = h
                    sched.add(c)


        ret_services = all_obj['service']
        for ret_s in ret_services:
            s = sched.services.find_srv_by_name_and_hostname(ret_s.host_name, ret_s.service_description)
            if s != None:
#                print "Ok, got data for", s.get_dbg_name()
#                print "Latency", ret_s.latency, type(ret_s.latency)
                running_properties = s.__class__.running_properties
                for prop in running_properties:
                    entry = running_properties[prop]
                    if 'retention' in entry and entry['retention']:
#                        print "Set service value", getattr(ret_s, prop)
                        setattr(s, prop, getattr(ret_s, prop))
                for a in s.notifications_in_progress.values():
                    a.ref = s
                    sched.add(a)
                s.update_in_checking()
                #And also add downtimes and comments
                for dt in s.downtimes:
                    dt.ref = s
                    sched.add(dt)
                for c in s.comments:
                    c.ref = s
                    sched.add(c)


        log_mgr.log("[NagiosRetention] OK we've load data from retention file")

        return True

