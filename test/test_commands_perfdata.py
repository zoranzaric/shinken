#!/usr/bin/env python2.6
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

#
# This file is used to test acknowledge of problems
#


#It's ugly I know....
from shinken_test import *

class TestConfig(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_commands_perfdata.cfg')


    def test_service_perfdata_command(self):
        self.print_header()

        #We want an eventhandelr (the perfdata command) to be put in the actions dict
        #after we got a service check
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        print "Service perfdata command", svc.__class__.perfdata_command, type(svc.__class__.perfdata_command)
        #We do not want to be just a string but a real command
        self.assert_(not isinstance(svc.__class__.perfdata_command, str))
        print svc.__class__.perfdata_command.__class__.my_type
        self.assert_(svc.__class__.perfdata_command.__class__.my_type == 'CommandCall')
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        print "Actions", self.sched.actions
        self.assert_(self.count_actions() == 1)

        #Ok now I disable the perfdata
        now = time.time()
        cmd = "[%lu] DISABLE_PERFORMANCE_DATA" % now
        self.sched.run_external_command(cmd)
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        print "Actions", self.sched.actions
        self.assert_(self.count_actions() == 0)


    def test_host_perfdata_command(self):
        #We want an eventhandelr (the perfdata command) to be put in the actions dict
        #after we got a service check
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        print "Host perfdata command", host.__class__.perfdata_command, type(host.__class__.perfdata_command)
        #We do not want to be just a string but a real command
        self.assert_(not isinstance(host.__class__.perfdata_command, str))
        print host.__class__.perfdata_command.__class__.my_type
        self.assert_(host.__class__.perfdata_command.__class__.my_type == 'CommandCall')
        self.scheduler_loop(1, [[host, 0, 'UP | bibi=99%']])
        print "Actions", self.sched.actions
        self.assert_(self.count_actions() == 1)

        #Ok now I disable the perfdata
        now = time.time()
        cmd = "[%lu] DISABLE_PERFORMANCE_DATA" % now
        self.sched.run_external_command(cmd)
        self.scheduler_loop(1, [[host, 0, 'UP | bibi=99%']])
        print "Actions", self.sched.actions
        self.assert_(self.count_actions() == 0)


if __name__ == '__main__':
    unittest.main()
