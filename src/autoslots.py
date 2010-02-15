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

#The AutoSlots Class is a MetaClass : it manage how other classes
#are created (Classes, not instances of theses classes).
#Here it's role is to create the __slots__ list of the class with
#all properties of Class.properties and Class.running_properties
#so we do not have to add manually all properties to the __slots__
#list when we add a new entry

class AutoSlots(type):
    #new is call when we create a new Class 
    #that have metaclass = AutoSlots
    #CLS is AutoSlots
    #name is s tring of the Class (like Service)
    #bases are the Classes of which Class inherits (like SchedulingItem)
    #dct is the new Class dict (like all method of Service)
    #Some properties name are not alowed in __slots__ like 2d_coords of
    #Host, so we must tag them in properties with no_slots
    def __new__(cls, name, bases, dct):
        slots = dict.fromkeys(dct.get('__slots__', []))
        #Now get properties from properties and running_properties
        if 'properties' in dct:
            for prop in dct['properties']:
                if not 'no_slots' in dct['properties'][prop] or not dct['properties'][prop]['no_slots']:
                    slots[prop] = None
        if 'running_properties' in dct:
            for prop in dct['running_properties']:
                if not 'no_slots' in dct['running_properties'][prop] or not dct['running_properties'][prop]['no_slots']:
                    slots[prop] = None
        dct['__slots__'] = list(set(slots.keys()))
        return type.__new__(cls, name, bases, dct)