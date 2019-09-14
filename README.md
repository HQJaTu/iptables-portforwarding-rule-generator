# iptables Port Forwarding Rule Generator
This Python 3.x application is a Linux port forwarding rule generator from an YAML file into executable iptables commands.

Video games on PC or console have multiple requirements for port forwarding and maintaining the commands can be tricky.
Having human-readable rule-files is much easier to create and mantain. This utility is intended to aid in that task. 

# Running
Execute `portforward-yaml-to-iptables.py` to process a rules-file and
output Bash-commands into standard output.

## Example run

Create iptables-rules to add port-forwarding into a router for [Wreckfest](https://order.wreckfestgame.com/) multiplayer game.
* Bash shell is required for single-line flush/create the chain
* The router IP-address is irrelevant, these rules are run into the router receiving Internet traffic
* Destination host running the game server is: _192.168.0.5_
* Network interface used for forwarding is: _eth1_

```bash
$ ./portforward-yaml-to-iptables.py Sample\ rules/Wreckfest.yaml 192.168.0.5 eth1
Processing rules for: wreckfest
iptables -t nat -F wreckfest > /dev/null || iptables -t nat -N wreckfest
iptables -t nat -A PREROUTING -i eth1 -j wreckfest
iptables -t nat -A wreckfest -p tcp -m multiport --dports 27015:27030 -j DNAT --to-destination 192.168.0.5
iptables -t nat -A wreckfest -p tcp -m multiport --dports 27036:27037 -j DNAT --to-destination 192.168.0.5
iptables -t nat -A wreckfest -p udp -m udp --dport 4380 -j DNAT --to-destination 192.168.0.5
iptables -t nat -A wreckfest -p udp -m multiport --dports 27000:27031 -j DNAT --to-destination 192.168.0.5
iptables -t nat -A wreckfest -p udp -m udp --dport 27036 -j DNAT --to-destination 192.168.0.5
iptables -t nat -A wreckfest -p udp -m udp --dport 33540 -j DNAT --to-destination 192.168.0.5
```

# Rules-file explained

There are three parts in a file:
 1. iptables chain name
 1. (optional) TCP port forwarding rules
 1. (optional) UDP port forwarding rules

```yaml

---
rules:
  # iptables chain name
  - chain-name: wreckfest
  # TCP port forwarding rules
    tcp:
      - <single port>
      - <lower port of a range>-<higher port of a range>
      - <another single port>
  # UDP port forwarding rules
    udp:
      - <single port>
```

# Example rules
See directory `Sample rules` for actual real-life examples.