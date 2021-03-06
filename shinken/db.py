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


#DB is a generic class for SQL Database

class DB(object):
    def __init__(self, table_prefix = ''):
        self.table_prefix = table_prefix

    # Get a unicode from a value
    def stringify(self, val):
        # If raw string, go in unicode
        if isinstance(val, str):
            val = val.decode('utf8', 'ignore').replace("'", "''")
        elif isinstance(val, unicode):
            val = val.replace("'", "''")
        else: # other type, we can str
            val = unicode(str(val))
            val = val.replace("'", "''")
        return val


    #Create a INSERT query in table with all data of data (a dict)
    def create_insert_query(self, table, data):
        query = u"INSERT INTO %s " % (self.table_prefix + table)
        props_str = u' ('
        values_str = u' ('
        i = 0 #for the ',' problem... look like C here...
        for prop in data:
            i += 1
            val = data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0

            # Get a string of the value
            val = self.stringify(val)

            if i == 1:
                props_str = props_str + u"%s " % prop
                values_str = values_str + u"'%s' " % val
            else:
                props_str = props_str + u", %s " % prop
                values_str = values_str + u", '%s' " % val

        #Ok we've got data, let's finish the query
        props_str = props_str + u' )'
        values_str = values_str + u' )'
        query = query + props_str + u' VALUES' + values_str
        return query


    #Create a update query of table with data, and use where data for
    #the WHERE clause
    def create_update_query(self, table, data, where_data):
        query = u"UPDATE %s set " % (self.table_prefix + table)

        #First data manage
        query_folow = ''
        i = 0 #for the , problem...
        for prop in data:
            #Do not need to update a property that is in where
            #it is even dangerous, will raise a warning
            if prop not in where_data:
                i += 1
                val = data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
                if isinstance(val, bool):
                    if val:
                        val = 1
                    else:
                        val = 0

                # Get a string of the value
                val = self.stringify(val)

                if i == 1:
                    query_folow += u"%s='%s' " % (prop, val)
                else:
                    query_folow += u", %s='%s' " % (prop, val)

        #Ok for data, now WHERE, same things
        where_clause = u" WHERE "
        i = 0 # For the 'and' problem
        for prop in where_data:
            i += 1
            val = where_data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0


            # Get a string of the value
            val = self.stringify(val)

            if i == 1:
                where_clause += u"%s='%s' " % (prop, val)
            else:
                where_clause += u"and %s='%s' " % (prop, val)

        query = query + query_folow + where_clause
        return query


    #Just get an entry
    def fetchone(self):
        return self.db_cursor.fetchone()
