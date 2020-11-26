#!/bin/bash

# br_ext
#ovs_mac2=fa:5d:6f:c7:05:af
#ovs_mac1=fa5d6fc705af
intf=enp0s9
mitm_ip=192.168.2.2
mitm_ip_16=c0a80202
trace_pkt="sudo ovs-appctl ofproto/trace br0"
# consider DHCP, ARP, DNS

# add flow for traffic from client to mitm
# Need to change mac everytime restart
function add-flow() {
  get-mac
  ovs-ofctl del-flows br0
  # 3 is br-ext port num, while 1 is port num of client
#  ovs-ofctl add-flow br0 -O openflow13 "priority=200,in_port=$intf,tcp,tp_dst=443, \
#  actions=load:3->reg0[0..3],load:1->reg0[4..7],\
#  learn(priority=320,table=0,dl_type=0x800,nw_proto=6,nw_src,nw_dst,tp_src,tp_dst,load:0x$ovs_mac1->dl_dst,load:0x$mitm_ip_16->nw_dst,load:3129->tp_dst,output:reg0[0..3]),\
#  learn(priority=310,table=0,dl_type=0x800,nw_proto=6,nw_src=$mitm_ip,nw_dst=nw_src,tp_src=3129,tp_dst=tp_src,load:nw_dst->nw_src,load:443->tp_src,output:reg0[4..7]),\
#  mod_dl_dst:$ovs_mac2,mod_nw_dst:$mitm_ip,mod_tp_dst:3129,output:br-ext"
#
#  ovs-ofctl add-flow br0 -O openflow13 "priority=200,in_port=$intf,tcp,tp_dst=80, \
#  actions=load:3->reg0[0..3],load:1->reg0[4..7],\
#  learn(priority=220,table=0,dl_type=0x800,nw_proto=6,nw_src,nw_dst,tp_src,tp_dst,load:0x$ovs_mac1->dl_dst,load:0x$mitm_ip_16->nw_dst,load:3128->tp_dst,output:reg0[0..3]),\
#  learn(priority=210,table=0,dl_type=0x800,nw_proto=6,nw_src=$mitm_ip,nw_dst=nw_src,tp_src=3128,tcp_dst=tcp_src,load:nw_dst->nw_src,load:80->tp_src,output:reg0[4..7]),\
#  mod_dl_dst:$ovs_mac2,mod_nw_dst:$mitm_ip,mod_tp_dst:3128,output:br-ext"
#
#  ovs-ofctl add-flow br0 -O openflow13 priority=0,actions=normal

  ovs-ofctl add-flow br0 -O openflow13 "priority=200,in_port=$intf,tcp,tp_dst=80, \
  actions=load:3->reg0[0..3],load:1->reg0[4..7],\
  learn(priority=220,table=0,dl_type=0x800,nw_proto=6,nw_src,nw_dst,tp_src,tp_dst,load:0x$ovs_mac1->dl_dst,load:0x$mitm_ip_16->nw_dst,load:3128->tp_dst,output:reg0[0..3]),\
  learn(priority=210,table=0,dl_type=0x800,nw_proto=6,nw_src=$mitm_ip,nw_dst=nw_src,tp_src=3128,tcp_dst=tcp_src,load:nw_dst->nw_src,load:80->tp_src,output:reg0[4..7]),\
  mod_dl_dst:$ovs_mac2,mod_nw_dst:$mitm_ip,mod_tp_dst:3128,output:br-ext"

  ovs-ofctl add-flow br0 -O openflow13 priority=0,actions=normal
}

# simulate a client session
function test-session() {
  if [ "$2" -eq 443 ]; then
    port=3129
  elif [ "$2" -eq 80 ]; then
    port=3128
  fi
  printf "%s %d\n===================\n" "first packet, client -> server" "$1"
  $trace_pkt in_port=1,tcp,nw_src=192.168.2.3,nw_dst=8.8.8.8,tp_src="$1",tp_dst="$2" --generate
  printf "\n%s %d\n=================\n" "second packet, client -> server" "$1"
  $trace_pkt in_port=1,tcp,nw_src=192.168.2.3,nw_dst=8.8.8.8,tp_src="$1",tp_dst="$2"
  printf "\n%s %d\n=================\n" "third packet, server -> client" "$1"
  $trace_pkt in_port=3,tcp,nw_src=192.168.2.2,nw_dst=192.168.2.3,tp_src=$port,tp_dst="$1"
  printf "\n=====================\n"
}

# test a packet going to proxy
function test-normal() {
  printf "%s\n===================\n" "packet, mitm -> proxy"
  $trace_pkt in_port=3,tcp,nw_src=192.168.2.2,nw_dst=192.168.2.1,tp_src=1234,tp_dst=443
  printf "\n%s\n===================\n" "packet, proxy -> mitm"
  $trace_pkt in_port=2,tcp,nw_src=192.168.2.1,nw_dst=192.168.2.2,tp_src=443,tp_dst=1234
  printf "\n=====================\n"
}

function test-flow() {
  test-session 1234 443
  test-session 5678 443
  test-session 4321 80
  test-session 8765 80
  test-normal
}

get-mac() {
  ovs_mac2=$(ovs-vsctl get interface br-ext mac-in-use | sed 's/"//g')
  echo "$ovs_mac2"
  ovs_mac1=$(echo "$ovs_mac2" | sed 's/[:"]//g')
  echo "$ovs_mac1"
}

debug() {
  $trace_pkt in_port=1,tcp,nw_src=192.168.2.3,nw_dst=13.33.201.71,tp_src=12345,tp_dst=80 --generate
  $trace_pkt in_port=3,tcp,nw_src=192.168.2.2,nw_dst=192.168.2.3,tp_src=3128,tp_dst=12345
  sleep 1
  printf "\n%s %d\n=================\n" "second packet, client -> server" "$1"
  $trace_pkt in_port=1,tcp,nw_src=192.168.2.3,nw_dst=13.33.201.42,tp_src=52345,tp_dst=80 --generate
  $trace_pkt in_port=3,tcp,nw_src=192.168.2.2,nw_dst=192.168.2.3,tp_src=3128,tp_dst=52345
}

"$@"
