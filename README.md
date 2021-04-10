# proxany

Proxany is an proxy forwarding software that redirects your packets to your existing proxy server. You do not have to configure anything for proxy settings on your computer. Proxany makes your proxy behave like a transparent proxy.

## Where you can use Proxany

When you have a application that needs to download some files from the Internet through http/https,

but it fail to connect because proxy setting is not configured properly. But you cannot or don't know how to get it configured for that application.

In this situation, the Proxany is just for you! With proxany, you simply install it on a computer and put this computer between your computer and the network.

Then Proxany will redircet your http/https traffic to the proxy server. Users do not worry about how to configure the proxy setting.

Save your time for more important thing!

## Supported Protocols

Currently the following protocols are supported:
* HTTP - 80
* HTTPS - 443

## Architecture

![alt text](https://github.com/jamescch/proxany/blob/master/arch.png)

## Installation
### Prerequisites

There should be a Proxy server already in your network.

And a computer for installing Proxany should have:
* Linux OS
* At least two network interfaces
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

* ```client_port="enp0s8"```  The interface that connects to your computer.

* ```ext_port="enp0s10"```    The interface that connects to the network.

* ```mgmt_ip_cidr=192.168.56.3/24``` The IP address on the client interface. This is used for management.

* ```data_ip_cidr=192.168.2.2/24```  The IP address on the external interface. This is used to communicate with the proxy server.

* ```proxy_ip=192.168.2.1``` The IP address of proxy server.

* ```proxy_port=3128``` The serving port of proxy server.

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

