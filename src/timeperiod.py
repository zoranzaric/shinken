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


#Calendar date: '(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) / (\d+) ([0-9:, -]+)' => len = 8  => CALENDAR_DATE
#               '(\d{4})-(\d{2})-(\d{2}) / (\d+) ([0-9:, -]+)' => len = 5 => CALENDAR_DATE
#               '(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) ([0-9:, -]+)' => len = 7 => CALENDAR_DATE
#               '(\d{4})-(\d{2})-(\d{2}) ([0-9:, -]+)' => len = 4 => CALENDAR_DATE
#
#Month week day:'([a-z]*) (\d+) ([a-z]*) - ([a-z]*) (\d+) ([a-z]*) / (\d+) ([0-9:, -]+)' => len = 8 => MONTH WEEK DAY
#               ex: wednesday 1 january - thursday 2 july / 3
#
#               '([a-z]*) (\d+) - ([a-z]*) (\d+) / (\d+) ([0-9:, -]+)' => len = 6
#               ex: february 1 - march 15 / 3 => MONTH DATE
#               ex: monday 2 - thusday 3 / 2 => WEEK DAY
#               ex: day 2 - day 6 / 3 => MONTH DAY
#
#               '([a-z]*) (\d+) - (\d+) / (\d+) ([0-9:, -]+)' => len = 6
#               ex: february 1 - 15 / 3 => MONTH DATE
#               ex: thursday 2 - 4 => WEEK DAY
#               ex: day 1 - 4 => MONTH DAY
#
#               '([a-z]*) (\d+) ([a-z]*) - ([a-z]*) (\d+) ([a-z]*) ([0-9:, -]+)' => len = 7
#               ex: wednesday 1 january - thursday 2 july => MONTH WEEK DAY
#
#               '([a-z]*) (\d+) - (\d+) ([0-9:, -]+)' => len = 7
#               ex: thursday 2 - 4 => WEEK DAY
#               ex: february 1 - 15 / 3 => MONTH DATE
#               ex: day 1 - 4 => MONTH DAY
#
#               '([a-z]*) (\d+) - ([a-z]*) (\d+) ([0-9:, -]+)' => len = 5
#               ex: february 1 - march 15  => MONTH DATE
#               ex: monday 2 - thusday 3  => WEEK DAY
#               ex: day 2 - day 6  => MONTH DAY
#
#               '([a-z]*) (\d+) ([0-9:, -]+)' => len = 3
#               ex: february 3 => MONTH DATE
#               ex: thursday 2 => WEEK DAY
#               ex: day 3 => MONTH DAY
#
#               '([a-z]*) (\d+) ([a-z]*) ([0-9:, -]+)' => len = 4
#               ex: thusday 3 february => MONTH WEEK DAY
#
#               '([a-z]*) ([0-9:, -]+)' => len = 6
#               ex: thusday => normal values
#               
#Types: CALENDAR_DATE              
#       MONTH WEEK DAY        
#       WEEK DAY
#       MONTH DATE
#       MONTH DAY
#
import re, time, calendar

from item import Item, Items
from util import *
from memoized import memoized


from daterange import Daterange,CalendarDaterange,StandardDaterange,MonthWeekDayDaterange
from daterange import MonthDateDaterange,WeekDayDaterange,MonthDayDaterange
from daterange import Timerange


class Timeperiod:
    id = 0

    my_type = 'timeperiod'
    
    def __init__(self, params={}):
        self.id = Timeperiod.id
        Timeperiod.id = Timeperiod.id + 1
        self.unresolved = []
        self.dateranges = []
        self.exclude = ''
        for key in params:
            if key in ['name', 'alias', 'timeperiod_name', 'exclude']:
                setattr(self, key, params[key])
            else:
                self.unresolved.append(key+' '+params[key])
        self.is_valid_today = False

        self.cache = {} #For tunning purpose only

    def get_name(self):
        return self.timeperiod_name
        

    def clean(self):
        pass


    def is_time_valid(self, t):
        if self.has('exclude'):
            for dr in self.exclude:
                if dr.is_time_valid(t):
                    return False
        for dr in self.dateranges:
            if dr.is_time_valid(t):
                return True
        return False


    #will give the first time > t which is valid
    def get_min_from_t(self, t):
        mins_incl = []
        for dr in self.dateranges:
            mins_incl.append(dr.get_min_from_t(t))
        return min(mins_incl)


    #will give the first time > t which is not valid
    def get_not_in_min_from_t(self, f):
        pass


    def find_next_valid_time_from_cache(self, t):
        try:
            return self.cache[t]
        except KeyError:
            return None


    #clean the get_next_valid_time_from_t cache
    #The entries are a dict on t. t < now are useless
    #Because we do not care about past anymore.
    #If not, it's not important, it's just a cache after all :)
    def clean_cache(self):
        now = int(time.time())
        t_to_del = []
        for t in self.cache:
            if t < now:
                t_to_del.append(t)
        for t in t_to_del:
            del self.cache[t]


    def get_next_valid_time_from_t(self, t):
        #first find from cache
        t = int(t)
        original_t = t
        
        #print self.get_name(), "Check valid time for", time.asctime(time.localtime(t))

        res_from_cache = self.find_next_valid_time_from_cache(t)
        if res_from_cache is not None:
            return res_from_cache

        still_loop = True

        local_min = None
        #Loop for all minutes...
        while still_loop:
            #print self.get_name(), '\nLoop'
            #Ok, not in cache...
            dr_mins = []
            for dr in self.dateranges:
                dr_mins.append(dr.get_next_valid_time_from_t(t))
            
            #print self.get_name(), 'Mins:', dr_mins
            #for o in dr_mins:
            #    print self.get_name(), '\t',time.asctime(time.localtime(o))

            #Min but not the None valus...
            try:
                local_min = min([d for d in dr_mins if d!=None])
            except ValueError: #dr_mins if full of None, not good
                local_min = None

            #print self.get_name(), 'Local min:', local_min

            #We do not loop unless the local_min is not valid
            still_loop = False
            
            #if we've got a real value, we check it with the exclude
            if local_min != None:
                #Now check if local_min is not valid
                for tp in self.exclude:
                    #print self.get_name(), "Check in TP"
                    if tp.is_time_valid(local_min):
                        still_loop = True
                        #t = local_min + 60
                        #print self.get_name(), "TP pas content:", tp.get_name(), time.asctime(time.localtime(local_min))
                        local_min = tp.get_next_invalid_time_from_t(local_min+60)
                        #print self.get_name(), "Apres content:", tp.get_name(), time.asctime(time.localtime(local_min))
                    #else:
                    #    print self.get_name(), "Tp ca lui va", tp.get_name()
                        
            if local_min == None:
                still_loop = False
            else:
                #print 'Local min', local_min
                t = local_min
                #No loop more than one year
                if t > original_t + 3600*24*366 + 1:
                    still_loop = False
                    local_min = None

        #Ok, we update the cache...
        self.cache[original_t] = local_min
        return local_min


    def get_next_invalid_time_from_t(self, t):
        #print '\n\n', self.get_name(), 'search for next invalid from', time.asctime(time.localtime(t))
        t = int(t)
        original_t = t
        still_loop = True
        
        if not self.is_time_valid(t):
            return t
        
        local_min = t
        res = None
        #Loop for all minutes...
        while still_loop:
            #Ok, not in cache...
            #print self.get_name(), "Begin loop with", time.asctime(time.localtime(local_min))
            next_exclude = None
            for dr in self.exclude:
                m = dr.get_next_valid_time_from_t(local_min)
                if m != None:
                    #print time.asctime(time.localtime(m))
                    if next_exclude == None or m <= next_exclude:
                        next_exclude = m

            #Maybe the min of exclude is not valid, it is the min we can find.
            if next_exclude !=None and not self.is_time_valid(next_exclude):
                #print self.get_name(), "find a possible early exit for invalid ! with", time.asctime(time.localtime(next_exclude)) 
                res = next_exclude
                still_loop = False

            #But maybe we can find a better solution with next invalid of standart dateranges
            #print self.get_name(), "After valid of exclude, local_min =", time.asctime(time.localtime(local_min))
            for dr in self.dateranges:
                #print self.get_name(), "Search a next invalid from DR", time.asctime(time.localtime(local_min))
                m = dr.get_next_invalid_time_from_t(local_min)
                #print self.get_name(), "Dr give me next invalid", time.asctime(time.localtime(m))
                if m != None:
                    #print time.asctime(time.localtime(m))
                    local_min = m
            
            #print self.get_name(), 'Invalid: local min', time.asctime(time.localtime(local_min))
            #We do not loop unless the local_min is not valid
            still_loop = False
            
            #if we've got a real value, we check it with the exclude
            if local_min != None:
                #Now check if local_min is not valid
                for tp in self.exclude:
                    #print self.get_name(),"we check for invalid", time.asctime(time.localtime(local_min)), 'with tp', tp.name
                    if tp.is_time_valid(local_min):
                        still_loop = True
                        #local_min + 60
                        local_min = tp.get_next_invalid_time_from_t(local_min+60)
                        #No loop more than one year
                        if local_min > original_t + 60*24*366 + 1:
                            still_loop = False
                            res = None
                if not still_loop:#We find a possible value
                    #We take the result the minimal possible
                    if res == None or local_min < res:
                        res = local_min

        return res

    
    def has(self, prop):
        return hasattr(self, prop)


    def __str__(self):
        s = ''
        s += str(self.__dict__)+'\n'
        for elt in self.dateranges:
            s += str(elt)
            (start,end) = elt.get_start_and_end_time()
            start = time.asctime(time.localtime(start))
            end = time.asctime(time.localtime(end))
            s += "\nStart and end:"+str((start, end))
        s += '\nExclude'
        for elt in self.exclude:
            s += str(elt)
                    
        return s

        
    def resolve_daterange(self, dateranges, entry):
        #print "Trying to resolve ", entry

        res = re.search('(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 1"
            (syear, smon, smday, eyear, emon, emday, skip_interval, other) = res.groups()
            dateranges.append(CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, skip_interval, other))
            return
        
        res = re.search('(\d{4})-(\d{2})-(\d{2}) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Good catch 2"
            (syear, smon, smday, skip_interval, other) = res.groups() 
            eyear = syear
            emon = smon
            emday = smday
            dateranges.append(CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, skip_interval, other))
            return

        res = re.search('(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2})[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 3"
            (syear, smon, smday, eyear, emon, emday, other) = res.groups()
            dateranges.append(CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, 0, other))
            return

        res = re.search('(\d{4})-(\d{2})-(\d{2})[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 4"
            (syear, smon, smday, other) = res.groups()
            eyear = syear
            emon = smon
            emday = smday
            dateranges.append(CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, 0, other))
            return

        res = re.search('([a-z]*) ([\d-]+) ([a-z]*) - ([a-z]*) ([\d-]+) ([a-z]*) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 5"
            (swday, swday_offset, smon, ewday, ewday_offset, emon, skip_interval, other) = res.groups()
            dateranges.append(MonthWeekDayDaterange(0, smon, 0, swday, swday_offset, 0, emon, 0, ewday, ewday_offset, skip_interval, other))
            return
        
        res = re.search('([a-z]*) ([\d-]+) - ([a-z]*) ([\d-]+) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 6"
            (t0, smday, t1, emday, skip_interval, other) = res.groups()
            if t0 in Daterange.weekdays and t1 in Daterange.weekdays:
                swday = t0
                ewday = t1
                swday_offset = smday
                ewday_offset = emday
                dateranges.append(WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,0,0, ewday, ewday_offset, skip_interval, other))
                return
            elif t0 in Daterange.months and t1 in Daterange.months:
                smon = t0
                emon = t1
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0,skip_interval,other))
                return
            elif t0 == 'day' and t1 == 'day':
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday, 0,0,skip_interval, other))
                return

        res = re.search('([a-z]*) ([\d-]+) - ([\d-]+) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 7"
            (t0, smday, emday, skip_interval, other) = res.groups()
            if t0 in Daterange.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = emday
                dateranges.append(WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,0,0, ewday, ewday_offset, skip_interval, other))
                return
            elif t0 in Daterange.months:
                smon = t0
                emon = smon
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0,skip_interval, other))
                return
            elif t0 == 'day':
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday,0,0,skip_interval,other))
                return


        res = re.search('([a-z]*) ([\d-]+) ([a-z]*) - ([a-z]*) ([\d-]+) ([a-z]*) [\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 8"
            (swday, swday_offset, smon, ewday, ewday_offset, emon, other) = res.groups()
            #print "Debug:", (swday, swday_offset, smon, ewday, ewday_offset, emon, other)
            dateranges.append(MonthWeekDayDaterange(0, smon, 0, swday, swday_offset, 0, emon, 0, ewday, ewday_offset, 0, other))
            return

        
        res = re.search('([a-z]*) ([\d-]+) - ([\d-]+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 9"
            (t0, smday, emday, other) = res.groups()
            if t0 in Daterange.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = emday
                dateranges.append(WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,0,0, ewday, ewday_offset, 0, other))
                return
            elif t0 in Daterange.months:
                smon = t0
                emon = smon
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0, 0, other))
                return
            elif t0 == 'day':
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday,0,0,0,other))
                return

        res = re.search('([a-z]*) ([\d-]+) - ([a-z]*) ([\d-]+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Googd catch 10"
            (t0, smday, t1, emday, other) = res.groups()
            if t0 in Daterange.weekdays and t1 in Daterange.weekdays:
                swday = t0
                ewday = t1
                swday_offset = smday
                ewday_offset = emday
                dateranges.append(WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,0,0, ewday, ewday_offset, 0, other))
                return
            elif t0 in Daterange.months and t1 in Daterange.months:
                smon = t0
                emon = t1
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0, 0,other))
                return
            elif t0 == 'day' and t1 == 'day':
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday, 0,0, 0, other))
                return

        res = re.search('([a-z]*) ([\d-]+) ([a-z]*)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            #print "Good catch 11"
            (t0, swday_offset, t1,other) = res.groups()
            if t0 in Daterange.weekdays and t1 in Daterange.months:
                swday = t0
                smon = t1
                emon = smon
                ewday = swday
                ewday_offset = swday_offset
                dateranges.append(MonthWeekDayDaterange(0, smon, 0, swday, swday_offset,0,emon,0,ewday,ewday_offset,0,other))
                return

        res = re.search('([a-z]*) ([\d-]+)[\s\t]+([0-9:, -]+)', entry)
        if res is not None:
            #print "Good catch 12"
            (t0, smday, other) = res.groups()
            if t0 in Daterange.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = swday_offset
                dateranges.append(WeekDayDaterange(0,0,0,swday,swday_offset,0,0,0,ewday,ewday_offset,0,other))
                return
            if t0 in Daterange.months:
                smon = t0
                emon = smon
                emday = smday
                dateranges.append(MonthDateDaterange(0, smon, smday, 0,0,0,emon,emday,0,0, 0,other))
                return
            if t0 == 'day':
                emday = smday
                dateranges.append(MonthDayDaterange(0,0,smday,0,0,0,0,emday, 0,0, 0, other))
                return

        res = re.search('([a-z]*)[\s\t]+([0-9:, -]+)', entry)
        if res is not None:
            #print "Good catch 13"
            (t0, other) = res.groups()
            if t0 in Daterange.weekdays:
                day = t0
                dateranges.append(StandardDaterange(day, other))
                return
        print "No match for", entry

    
    #create daterange from unresolved param
    def explode(self, timeperiods):
        for entry in self.unresolved:
            #print "Revolving entry", entry
            self.resolve_daterange(self.dateranges, entry)
        self.unresolved = []


    #Will make tp in exclude with id of the timeperiods
    def linkify(self, timeperiods):
        new_exclude = []
        if self.has('exclude') and self.exclude != '':
            print "I have excluded"
            print self.get_name(), self.exclude
            excluded_tps = self.exclude.split(',')
            #print "I will exclude from:", excluded_tps
            for tp_name in excluded_tps:
                tp = timeperiods.find_by_name(tp_name.strip())
                if tp != None:
                    new_exclude.append(tp)
                else:
                    print "Error : the timeperiod", tp_name, "is unknown!"
        self.exclude = new_exclude
        print "New exclude", self.exclude


    def check_exclude_rec(self):
        if self.rec_tag:
            print "Error :", self.get_name(), "is in a loop in exclude parameter"
            return
        self.rec_tag = True
        for tp in self.exclude:
            tp.check_exclude_rec()


class Timeperiods(Items):
    name_property = "timeperiod_name"
    inner_class = Timeperiod

                                   
    def explode(self):
        for id in self.items:
            tp = self.items[id]
            tp.explode(self)


    def linkify(self):
        for id in self.items:
            tp = self.items[id]
            tp.linkify(self)


    #check for loop in definition
    def is_correct(self):
        #We do not want a same hg to be explode again and again
        #so we tag it
        for tp in self.items.values():
            tp.rec_tag = False

        for tp in self.items.values():
            for tmp_tp in self.items.values():
                tmp_tp.rec_tag = False
            tp.check_exclude_rec()

        #We clean the tags
        for tp in self.items.values():
            del tp.rec_tag


        
            


if __name__ == '__main__':
    t = Timeperiod()
    test = ['1999-01-28	 00:00-24:00',
            'monday 3			00:00-24:00		',
            'day 2			00:00-24:00',
            'february 10		00:00-24:00',
            'february -1 00:00-24:00',
            'friday -2			00:00-24:00',
            'thursday -1 november 00:00-24:00',
            '2007-01-01 - 2008-02-01	00:00-24:00',
            'monday 3 - thursday 4	00:00-24:00',
            'day 1 - 15		00:00-24:00',
            'day 20 - -1		00:00-24:00',
            'july -10 - -1		00:00-24:00',
            'april 10 - may 15		00:00-24:00',
            'tuesday 1 april - friday 2 may 00:00-24:00',
            '2007-01-01 - 2008-02-01 / 3 00:00-24:00',
            '2008-04-01 / 7		00:00-24:00',
            'day 1 - 15 / 5		00:00-24:00',
            'july 10 - 15 / 2 00:00-24:00',
            'tuesday 1 april - friday 2 may / 6 00:00-24:00',
            'tuesday 1 october - friday 2 may / 6 00:00-24:00',
            'monday 3 - thursday 4 / 2 00:00-24:00',
            'monday 4 - thursday 3 / 2 00:00-24:00',
            'day -1 - 15 / 5		01:00-24:00,00:30-05:60',
            'tuesday 00:00-24:00',
            'sunday 00:00-24:00',
            'saturday 03:00-24:00,00:32-01:02',
            'wednesday 09:00-15:46,00:00-21:00',
            'may 7 - february 2 00:00-10:00',
            'day -1 - 5 00:00-10:00',
            'tuesday 1 february - friday 1 may 01:00-24:00,00:30-05:60',
            'december 2 - may -15		00:00-24:00',
            ]
    for entry in test:
        print "**********************"
        print entry
        t=Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, entry)
        #t.exclude = []
        #t.resolve_daterange(t.exclude, 'monday 00:00-19:00')
        #t.check_valid_for_today()
        now = time.time()
        #print "Is valid NOW?", t.is_time_valid(now)
        t_next = t.get_next_valid_time_from_t(now + 5*60)
        if t_next is not None:
            print "Get next valid for now + 5 min ==>", time.asctime(time.localtime(t_next)),"<=="
        else:
            print "===> No future time!!!"
        #print "Is valid?", t.is_valid_today
        #print "End date:", t.get_end_time()
        #print "Next valid", time.asctime(time.localtime(t.get_next_valid_time()))
        print str(t)+'\n\n'

    print "*************************************************************"
    t3 = Timeperiod()
    t3.timeperiod_name = 't3'
    t3.resolve_daterange(t3.dateranges, 'day 1 - 10 10:30-15:00')
    t3.exclude = []

    t2 = Timeperiod()
    t2.timeperiod_name = 't2'
    t2.resolve_daterange(t2.dateranges, 'day 1 - 10 12:00-17:00')
    t2.exclude = [t3]


    t = Timeperiod()
    t.timeperiod_name = 't'
    t.resolve_daterange(t.dateranges, 'day 1 - 10 14:00-15:00')
    t.exclude = [t2]

    print "Mon T",str(t)+'\n\n'
    t_next = t.get_next_valid_time_from_t(now)
    t_no_next = t.get_next_invalid_time_from_t(now)
    print "Get next valid for now ==>", time.asctime(time.localtime(t_next)),"<=="
    print "Get next invalid for now ==>", time.asctime(time.localtime(t_no_next)),"<=="

