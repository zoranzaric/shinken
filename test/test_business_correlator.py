#!/usr/bin/env python2.6
# Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *


class TestConfig(ShinkenTest):
    # Uncomment this is you want to use a specific configuration
    # for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_business_correlator.cfg')

    
    # We will try a simple bd1 OR db2
    def test_simple_or_business_correlator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule == None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule == None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule != None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '|')

        sons = bp_rule.sons
        print "Sons,", sons
        #We(ve got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)
        
        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])        
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')
        
        state = bp_rule.get_state()
        self.assert_(state == 0)
        
        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assert_(state == 0)
        
        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)
        
        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)
        
        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assert_(state == 1)



    # We will try a simple bd1 AND db2
    def test_simple_and_business_correlator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule == None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule == None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_And")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule != None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '&')

        sons = bp_rule.sons
        print "Sons,", sons
        #We(ve got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)
        
        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])        
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')
        
        state = bp_rule.get_state()
        self.assert_(state == 0)
        
        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assert_(state == 0)
        
        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)
        
        # The rule must go CRITICAL
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # Now we also set bd2 as WARNING/HARD...
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)
        
        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set one WARNING too?
        self.scheduler_loop(2, [[svc_bd1, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'WARNING')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 1)

        # Must be WARNING (worse no 0 value for both)
        state = bp_rule.get_state()
        self.assert_(state == 1)




    # We will try a simple 1of: bd1 OR/AND db2
    def test_simple_1of_business_correlator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule == None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule == None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_1Of")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule != None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        self.assert_(bp_rule.of_values == 1)
        
        
        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)
        
        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])        
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')
        
        state = bp_rule.get_state()
        self.assert_(state == 0)
        
        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assert_(state == 0)
        
        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)
        
        # The rule still be OK
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we also set bd2 as CRITICAL/HARD...
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)
        
        # And now the state of the rule must be 2 now
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set one WARNING now?
        self.scheduler_loop(2, [[svc_bd1, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'WARNING')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 1)

        # Must be WARNING (worse no 0 value for both, like for AND rule)
        state = bp_rule.get_state()
        self.assert_(state == 1)



    # We will try a simple bd1 OR db2, but this time we will
    # schedule a real check and see if it's good
    def test_simple_or_business_correlator_with_schedule(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule == None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule == None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule != None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '|')

        sons = bp_rule.sons
        print "Sons,", sons
        #We(ve got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)
        
        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')
        
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)
        

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        
        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)
        
        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)


        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)
        
        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)
        
        # And now we must be CRITICAL/SOFT!
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'CRITICAL')
        self.assert_(svc_cor.state_type == 'SOFT')
        self.assert_(svc_cor.last_hard_state_id == 0)

        #OK, re recheck again, GO HARD!
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'CRITICAL')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 2)


        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assert_(state == 1)

        # And in a HARD
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'WARNING')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 1)
        
        print "All elements", bp_rule.list_all_elements()

        print "IMPACT:", svc_bd2.impacts
        for i in svc_bd2.impacts:
            print i.get_name()

        # Assert that Simple_Or Is an impact of the problem bd2
        self.assert_(svc_cor in svc_bd2.impacts)
        # and bd1 too
        self.assert_(svc_cor in svc_bd1.impacts)


    def test_dep_node_list_elements(self):
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule == None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule == None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule != None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '|')

        print "All elements", bp_rule.list_all_elements()
        all_elt = bp_rule.list_all_elements()

        self.assert_(svc_bd2 in all_elt)
        self.assert_(svc_bd1 in all_elt)

        print "DBG: bd2 depend_on_me", svc_bd2.act_depend_of_me

    # We will try a full ERP rule and
    # schedule a real check and see if it's good
    def test_full_erp_rule_with_schedule(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule == None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule == None)
        svc_web1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "web1")
        self.assert_(svc_web1.got_business_rule == False)
        self.assert_(svc_web1.business_rule == None)
        svc_web2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "web2")
        self.assert_(svc_web2.got_business_rule == False)
        self.assert_(svc_web2.business_rule == None)
        svc_lvs1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs1")
        self.assert_(svc_lvs1.got_business_rule == False)
        self.assert_(svc_lvs1.business_rule == None)
        svc_lvs2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs2")
        self.assert_(svc_lvs2.got_business_rule == False)
        self.assert_(svc_lvs2.business_rule == None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "ERP")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule != None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '&')

        sons = bp_rule.sons
        print "Sons,", sons
        #We've got 3 sons, each 3 rules
        self.assert_(len(sons) == 3)
        bd_node = sons[0]
        self.assert_(bd_node.operand == '|')
        self.assert_(bd_node.sons[0].sons[0] == svc_bd1)
        self.assert_(bd_node.sons[1].sons[0] == svc_bd2)
        
        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')
        
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)
        

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        
        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)
        
        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)


        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)
        
        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)
        
        # And now we must be CRITICAL/SOFT!
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'CRITICAL')
        self.assert_(svc_cor.state_type == 'SOFT')
        self.assert_(svc_cor.last_hard_state_id == 0)

        #OK, re recheck again, GO HARD!
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'CRITICAL')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 2)


        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assert_(state == 1)

        # And in a HARD
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))
        
        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)
        
        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'WARNING')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 1)
        
        print "All elements", bp_rule.list_all_elements()

        print "IMPACT:", svc_bd2.impacts
        for i in svc_bd2.impacts:
            print i.get_name()

        # Assert that Simple_Or Is an impact of the problem bd2
        self.assert_(svc_cor in svc_bd2.impacts)
        # and bd1 too
        self.assert_(svc_cor in svc_bd1.impacts)

        # And now all is green :)
        self.scheduler_loop(2, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | value1=1 value2=2']])

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # And no more in impact
        self.assert_(svc_cor not in svc_bd2.impacts)
        self.assert_(svc_cor not in svc_bd1.impacts)

        # And what if we set 2 service from distant rule CRITICAL?
        # ERP should be still OK
        # And now all is green :)
        self.scheduler_loop(2, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2'], [svc_web1, 2, 'CRITICAL | value1=1 value2=2']])

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        #ask the scheduler to launch this check
        #and ask 2 loops: one for launch the check
        #and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)
        


if __name__ == '__main__':
    unittest.main()
