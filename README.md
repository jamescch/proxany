# proxany

Proxany is a proxy forwarding software that redirects your packets to your existing proxy server. You do not have to configure anything for proxy settings on your computer. Proxany makes your proxy behave like a transparent proxy.

## Where you can use Proxany

When you have an application that needs to download some files from the Internet through HTTP/HTTPS,

but it fails to connect because the proxy setting is not configured properly. But you cannot or don't know how to get it configured for that application.

In this situation, the Proxany is just for you! With proxany, you simply install it on a computer and put this proxany computer either between your computer and the network,
or somewhere reachable in the network.

Then Proxany will redirect your HTTP/HTTPS traffic to the proxy server. Users do not worry about how to configure the proxy setting.

Save your time for more important things!

## Supported Protocols

Currently the following protocols are supported:
* HTTP - 80
* HTTPS - 443

## Architecture

Two modes can be deployed on your preference.
Router mode is the default mode that the proxany computer is put in the network, mostly connected to a switch that can be reached by the user computer.
In this mode it is required to change the gateway IP on the user computer to the IP of proxany computer.

Interception mode is that the proxany computer is put between the user computer and the network. So the proxany can intercept the traffic.
In this mode there is no need to change any configuration on the user computer.

![alt text](https://github.com/jamescch/proxany/blob/master/arch.png)

## Installation
### Prerequisites

There should be a Proxy server already in your network.

And a computer for installing Proxany should have:
* Linux OS
* At least two network interfaces if using interception mode.
* Python 3.6 or later
* A free IP address that can communicate with the proxy server.

### Install from the repository
```
git clone https://github.com/jamescch/proxany.git
cd proxany/scripts
./install.sh
```

## Usage

### Configurations
To configure Proxany settings, please modify `scripts/proxany.sh`.

* ```ext_port=enp0s8``` The interface that connects to the network.
* ```data_ip_cidr=192.168.0.167/24``` The IP address on the external interface. This is used to communicate with the proxy server.
* ```gateway=192.168.0.1``` The IP address of gateway in the network.
* ```proxy_ip=192.168.0.142``` The IP address of proxy server.
* ```proxy_port=3128``` The serving port of proxy server.

#### Router mode

* ```mode=router```

On the user computer that desires to use proxany service,
change its default gateway to the proxany IP, which is the data_ip.

```ip r add default via data_ip```

#### Interception mode

* ```mode=interception```

Uncomment the following two variables below `[interception mode]` and set their value.
* ```client_port=enp0s8``` The interface that connects to the user computer.
* ```mgmt_ip_cidr=192.168.56.3/24``` The IP address on the client interface. This is used for management.

### Running

To start the program
```
scripts/proxany.sh start
```

To stop the program
```
scripts/proxany.sh stop
```

## Dependent Projects

Open vSwitch: OVS is used as packet processing tools.

## License

Apache 2.0

## Help / Contact

If you have any questions, please open an issue or contact us at greensun1231@gmail.com

