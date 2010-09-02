#!/bin/bash

set -x

echo "Begining test END TO END"


DIR=$(cd $(dirname "$0"); pwd)
echo "Going to dir $DIR/.."
cd $DIR/..

echo "Clean old tests and kill remaining processes"
./clean.sh

echo "Now we can start some launch tests"
bin/launch_all.sh


echo "Now checking for existing apps"


#check for a process existance with good number
function check_process_nb {
    NB=`ps -fu shinken | grep python | grep -v grep | grep $1 | wc -l`
    if [ $NB != "$2" ]
    then
	echo "Error : There is not enouth $1 launched (only $NB)."
	exit 2
    else
	echo "Ok, got $NB $1"
    fi
} 

function is_file_present {
    if [ -f $1 ]
    then
	echo "File $1 is present."
    else
	echo "Error : File $1 is missing!"
	exit 2
    fi
}

function string_in_file {
    grep "$1" $2
    if [ $? != 0 ]
    then
	echo "Error : the file $2 is missing string $1 !"
	exit 2
    else
	echo "The string $1 is in $2"
    fi
}


function check_good_run {
    VAR="$1"
    echo "Check for 1 Scheduler"
    check_process_nb scheduler 1
    is_file_present $VAR/schedulerd.pid
    
    echo "Check for 6 pollers (1 master, 1 for multiporcess module (queue manager), 4 workers)"
    check_process_nb poller 6
    is_file_present $VAR/pollerd.pid
    
    echo "Check for 2 reactionners (1 master, 1 for multiporcess module (queue manager) 1 worker)"
    check_process_nb reactionner 3
    is_file_present $VAR/reactionnerd.pid
    
    echo "Check for 2 brokers (one master, one for status.dat)"
    check_process_nb broker 2
    is_file_present $VAR/brokerd.pid
    
    echo "Check for 1 arbiter"
    check_process_nb arbiter 1
    is_file_present $VAR/arbiterd.pid
    
    echo "Now checking for good file prensence"
    ls var
    is_file_present $VAR/nagios.log
    string_in_file "Waiting for initial configuration" $VAR/nagios.log
    string_in_file "First scheduling" $VAR/nagios.log
    string_in_file "OK, all schedulers configurations are dispatched :)" $VAR/nagios.log
    string_in_file "OK, no more reactionner sent need" $VAR/nagios.log
    string_in_file "OK, no more poller sent need" $VAR/nagios.log
    string_in_file "OK, no more broker sent need" $VAR/nagios.log
}



echo "we can sleep 5sec for conf dispatching and so good number of process"
sleep 5

#Now check if the run looks good with var in the direct directory
check_good_run var

echo "First launch check OK"

echo "Now we clean it and test an install"
./clean.sh


echo "Now installing the application"
#python setup.py install --root=/tmp/moncul --record=INSTALLED_FILES --install-scripts=/usr/bin


echo "All check are OK. Congrats!"