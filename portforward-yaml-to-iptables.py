#!/usr/bin/env python3

# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import os
import argparse
import shlex

import yaml
import re
import ipaddress


def parse_rules(rules_file):
    rules = {}
    with open(rules_file, "r") as stream:
        rules_in = yaml.safe_load(stream)

    if 'rules' not in rules_in:
        print("Invalid rules-YAML %s! No 'rules' in it." % rules_file)
        exit(2)

    for rule_set_in in rules_in['rules']:
        rule_set = parse_rule_set(rule_set_in)
        rules[rule_set[0]] = rule_set[1:]

    return rules


def parse_rule_set(rule_set_in):
    if 'chain-name' not in rule_set_in:
        raise ValueError("Invalid rules-YAML! No 'chain-name' in it.")

    name = rule_set_in['chain-name']
    if not name or len(name) >= 30:
        raise ValueError("Invalid rules-YAML! Chain name '%s' is invalid! (length)")
    if not re.match(r'^\S+$', name):
        raise ValueError("Invalid rules-YAML! Chain name '%s' is invalid! (whitespace)")

    tcp_ports = []
    udp_ports = []
    if 'tcp' in rule_set_in and rule_set_in['tcp']:
        for tcp_rule_in in rule_set_in['tcp']:
            tcp_rule = parse_port_rule(tcp_rule_in)
            tcp_ports.append(tcp_rule)
    if 'udp' in rule_set_in and rule_set_in['udp']:
        for udp_rule_in in rule_set_in['udp']:
            udp_rule = parse_port_rule(udp_rule_in)
            udp_ports.append(udp_rule)

    if not tcp_ports and not udp_ports:
        raise ValueError("Invalid rules-YAML! No TCP nor UDP rules in it.")

    return name, tcp_ports, udp_ports


def parse_port_rule(rule_in):
    if not isinstance(rule_in, str):
        rule_in = str(rule_in)
    single_number_match = re.search(r'^(\d+)$', rule_in)
    if single_number_match:
        port = int(single_number_match.group(1))
        if port > 0 and port < 65535:
            return port

        raise ValueError("Rule '%s' isn't valid! Not a port number.")

    range_match = re.search(r'^(\d+)[-:](\d+)$', rule_in)
    if range_match:
        port_low = int(range_match.group(1))
        port_high = int(range_match.group(2))
        if port_low > 0 and port_low < 65535 and port_high > 0 and port_high < 65535 and port_high > port_low:
            return port_low, port_high

        raise ValueError("Rule '%s' isn't valid! Not a port range.")

    raise ValueError("Rule '%s' isn't valid!" % rule_in)


def rules_to_iptables(rules_in, destination_ip, source_interface):
    rules_out = []
    for rule_set_name in rules_in:
        print("Processing rules for: %s" % rule_set_name)
        rule_set = rules_in[rule_set_name]
        set_name_out = shlex.quote(rule_set_name)

        rules_out += ["iptables -t nat -F %s > /dev/null || iptables -t nat -N %s" % (set_name_out, set_name_out)]

        if source_interface:
            rules_out += ["iptables -t nat -A PREROUTING -i %s -j %s" % (source_interface, set_name_out)]
        else:
            rules_out += ["iptables -t nat -A PREROUTING -j \"%s\"" % set_name_out]

        for tcp_rule in rule_set[0]:
            if isinstance(tcp_rule, tuple):
                rules_out += ["iptables -t nat -A %s -p tcp -m multiport --dports %s -j DNAT --to-destination %s" %
                              (set_name_out, ':'.join(str(port) for port in tcp_rule), destination_ip)]
            else:
                rules_out += ["iptables -t nat -A %s -p tcp -m tcp --dport %s -j DNAT --to-destination %s" % (
                    set_name_out, tcp_rule, destination_ip)]
        for udp_rule in rule_set[1]:
            if isinstance(udp_rule, tuple):
                rules_out += ["iptables -t nat -A %s -p udp -m multiport --dports %s -j DNAT --to-destination %s" %
                              (set_name_out, ':'.join(str(port) for port in udp_rule), destination_ip)]
            else:
                rules_out += ["iptables -t nat -A %s -p udp -m udp --dport %s -j DNAT --to-destination %s" % (
                    set_name_out, udp_rule, destination_ip)]

    print('\n'.join(rules_out))


def main():
    parser = argparse.ArgumentParser(description='IPtables port forwarding rule generator')
    parser.add_argument('rules_file',
                        help='The YAML-file containing rules')
    parser.add_argument('destination_ip',
                        help='Destination IPv4 or IPv6 address to forward the ports to')
    parser.add_argument('source_interface', nargs='?',
                        help='Destination IPv4 or IPv6 address to forward the ports to')
    args = parser.parse_args()

    # Confirm args
    # YAML-rules file
    if not os.path.isfile(args.rules_file):
        print("YAML rules file '%s' doesn't exist!" % args.rules_file)
        exit(2)

    # Destination IP-address
    try:
        dest_ip = ipaddress.ip_address(args.destination_ip)
    except ValueError:
        print("Destination IP-address '%s' isn't valie!" % args.destination_ip)
        exit(2)

    rules = parse_rules(args.rules_file)
    if not rules:
        print("YAML rules file '%s' doesn't contain any rules in it!" % args.rules_file)
        exit(2)

    rules_to_iptables(rules, dest_ip, args.source_interface)


if __name__ == "__main__":
    main()
