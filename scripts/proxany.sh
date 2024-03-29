#!/bin/bash

# mode choices: router, interception
mode=router
ext_port=enp0s8
data_ip_cidr=192.168.0.167/24
gateway=192.168.0.1
proxy_ip=192.168.0.142
proxy_port=3128
# [interception mode]
# client_port=enp0s8
# mgmt_ip_cidr=192.168.56.3/24


data_ip=${data_ip_cidr%/*}
data_ip_16=$(printf '%02x' ${data_ip//./ })
data_port=3128
data_port_s=3129
client_port_num=
ext_port_num=

get-mac() {
  ovs_mac2=$(ip link show "$1" | grep ether | awk '{print $2}')
  echo "$ovs_mac2"
  ovs_mac1=$(echo "$ovs_mac2" | sed 's/[:"]//g')
  echo "$ovs_mac1"
}

get-port-num() {
  ext_port_num=$(ovs-vsctl get interface br-ext ofport)

  if [[ $mode == "interception" ]]; then
    client_port_num=$(ovs-vsctl get interface $client_port ofport)
  else
    client_port_num=$(ovs-vsctl get interface $ext_port ofport)
  fi
}

add-flow() {
  get-mac br-ext
  get-port-num
  ovs-ofctl del-flows br0

  extra_match=""
  if [[ $mode == "router" ]]; then
    extra_match="dl_dst=$ovs_mac2,"
    client_port=$ext_port
  fi

  ovs-ofctl add-flow br0 -O openflow13 "priority=200,in_port=$client_port,tcp,tp_dst=443,$extra_match \
  actions=load:$ext_port_num->reg0[0..3],load:$client_port_num->reg0[4..7],\
  learn(idle_timeout=0,fin_idle_timeout=10,priority=320,table=0,dl_type=0x800,nw_proto=6,nw_src,nw_dst,tp_src,tp_dst,load:0x$ovs_mac1->dl_dst,load:0x$data_ip_16->nw_dst,load:$data_port_s->tp_dst,output:reg0[0..3]),\
  learn(idle_timeout=0,fin_idle_timeout=10,priority=310,table=0,dl_type=0x800,nw_proto=6,nw_src=$data_ip,nw_dst=nw_src,tp_src=$data_port_s,tp_dst=tp_src,load:nw_dst->nw_src,load:443->tp_src,output:reg0[4..7]),\
  mod_dl_dst:$ovs_mac2,mod_nw_dst:$data_ip,mod_tp_dst:$data_port_s,output:br-ext"

  ovs-ofctl add-flow br0 -O openflow13 "priority=200,in_port=$client_port,tcp,tp_dst=80,$extra_match \
  actions=load:$ext_port_num->reg0[0..3],load:$client_port_num->reg0[4..7],\
  learn(idle_timeout=0,fin_idle_timeout=10,priority=220,table=0,dl_type=0x800,nw_proto=6,nw_src,nw_dst,tp_src,tp_dst,load:0x$ovs_mac1->dl_dst,load:0x$data_ip_16->nw_dst,load:$data_port->tp_dst,output:reg0[0..3]),\
  learn(idle_timeout=0,fin_idle_timeout=10,priority=210,table=0,dl_type=0x800,nw_proto=6,nw_src=$data_ip,nw_dst=nw_src,tp_src=$data_port,tcp_dst=tcp_src,load:nw_dst->nw_src,load:80->tp_src,output:reg0[4..7]),\
  mod_dl_dst:$ovs_mac2,mod_nw_dst:$data_ip,mod_tp_dst:$data_port,output:br-ext"

  ovs-ofctl add-flow br0 -O openflow13 priority=0,actions=normal
}

start() {
  if [ "$EUID" -ne 0 ]
    then echo "Please run as root"
    exit
  fi

  export PATH=$PATH:/usr/local/share/openvswitch/scripts
  ovs-ctl start

  if [[ $mode == "router" ]]; then
    sysctl -w net.ipv4.ip_forward=1

    ovs-vsctl --may-exist add-br br0
#    ip link set br0 up
    ip a flush $ext_port

    ovs-vsctl add-port br0 $ext_port
    ip link set $ext_port up

    ovs-vsctl --may-exist add-port br0 br-ext -- set interface br-ext type=internal

    get-mac $ext_port # for ext_port to keep connection, keep the same mac to br-ext
    ovs-vsctl set interface br-ext mac=\"$ovs_mac2\"

    ip link set br-ext up
    ip addr add $data_ip_cidr dev br-ext
    ip r add default via $gateway
  elif [[ $mode == "interception" ]]; then
    get-mac $client_port
    ovs-vsctl --may-exist add-br br0 -- set bridge br0 other-config:hwaddr=\"$ovs_mac2\"
    ip link set br0 up

    ip a add $mgmt_ip_cidr dev br0
    ip a flush $client_port
    ip a flush $ext_port

    ovs-vsctl add-port br0 $client_port
    ovs-vsctl add-port br0 $ext_port
    ip link set $client_port up
    ip link set $ext_port up

    ovs-vsctl --may-exist add-port br0 br-ext -- set interface br-ext type=internal

    macc=$(ovs-vsctl get interface br-ext mac-in-use)
    ovs-vsctl set interface br-ext mac="$macc"

    ip link set br-ext up
    ip addr add $data_ip_cidr dev br-ext
    ip r add default via $gateway
  fi



  add-flow

  if [[ $0 != *"scripts/proxany.sh"* ]]; then
    # must run from root directory
    cd ..
  fi
  sudo python3 proxany/proxy_fwd.py 0.0.0.0 $data_port $proxy_ip $proxy_port &> proxany.log &
}

stop() {
  if [ "$EUID" -ne 0 ]
    then echo "Please run as root"
    exit
  fi

  export PATH=$PATH:/usr/local/share/openvswitch/scripts
  if [[ $mode == "router" ]]; then
    sysctl -w net.ipv4.ip_forward=0
    ovs-vsctl del-port $ext_port
    ovs-ctl stop
    ip a flush br0
    ip a flush br-ext
    ip a add $data_ip_cidr dev $ext_port
  elif [[ $mode == "interception" ]]; then
    ovs-vsctl del-port $client_port # This will lose connection to client!
    ovs-vsctl del-port $ext_port
    ovs-ctl stop
    ip a flush br0
    ip a flush br-ext
    ip a add $mgmt_ip_cidr dev $client_port
  fi

  ps aux | grep proxany | awk '{print $2}' | xargs -r kill
}

help() {
  cat <<EOF
proxany 0.2.0
Usage: $0 COMMAND

commands:
  help         show help message
  start        start the proxany program
  stop         stop the proxany program
EOF
}

if [ $# -eq 0 ]
then
  help
  exit 1
fi

"$@"
