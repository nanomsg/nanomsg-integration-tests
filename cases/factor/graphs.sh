#!/bin/sh
RRDTOOL=${RRDTOOL:-rrdtool}
nworkers="$1"
timerange="--start $(< tmpcfg/start_timestamp) --end $(< tmpcfg/finish_timestamp)"
allmachines="master $(seq -fworker%.0f 0 $((nworkers-1)))"
declare -A colors

colors[master]=#FF0000
colors[worker0]=#0000FF
colors[worker1]=#0000C0
colors[worker2]=#FF00FF
colors[worker3]=#C000C0
colors[worker4]=#C0C0C0
colors[worker5]=#00FF00
colors[worker6]=#C0FF00

#colors[master]=#171A14
#colors[worker0]=#5C665A
#colors[worker1]=#4F5444
#colors[worker2]=#B5F2D5
#colors[worker3]=#82AE81

$RRDTOOL graph $timerange report/la.png \
    $(for i in $allmachines; do
    echo DEF:$i=rrd/$i/load/load.rrd:shortterm:AVERAGE LINE1:$i${colors[$i]}:$i;
    done)

$RRDTOOL graph $timerange report/msg_recv.png \
    $(for i in $allmachines; do
        cdef="CDEF:$i=0"
        for j in rrd/$i/*-socket.*/derive-messages_received.rrd; do
            name=${j//[^a-z0-9]/_}
            echo DEF:$name=$j:value:AVERAGE
            cdef="$cdef,$name,+"
        done
        echo $cdef
        echo AREA:$i${colors[$i]}:$i:STACK
    done)

$RRDTOOL graph $timerange report/msg_sent.png \
    $(for i in $allmachines; do
        cdef="CDEF:$i=0"
        for j in rrd/$i/*-socket.*/derive-messages_sent.rrd; do
            name=${j//[^a-z0-9]/_}
            echo DEF:$name=$j:value:AVERAGE
            cdef="$cdef,$name,+"
        done
        echo $cdef
        echo AREA:$i${colors[$i]}:$i:STACK
    done)
