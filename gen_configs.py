#!/usr/bin/env python3
"""Generate SR OS partial configs and strongSwan configs for the N:M SecGW lab."""
from pathlib import Path

OUT = Path(__file__).parent / "configs"

PSK = "ChangeMe-LabPsk"
GW_ADDR = "198.51.100.1"
CORE_AS, SEGW_AS = 65000, 64512

SEGW = {
    1: {"role": "active", "prio": 200},
    2: {"role": "active", "prio": 100},
    3: {"role": "standby", "prio": 200},
}

# Two MIMPv2/MCS links per SeGW pair, (lower-node port, higher-node port) for link A and link B.
# Must match the links in nm-mc-ipsec.clab.yml.
LINKS = {
    (1, 2): [("1/1/1", "1/1/1"), ("1/1/2", "1/1/2")],
    (1, 3): [("1/1/3", "1/1/1"), ("1/1/4", "1/1/2")],
    (2, 3): [("1/1/3", "1/1/3"), ("1/1/4", "1/1/4")],
}

BFD = "bfd { admin-state enable transmit-interval 100 receive 100 multiplier 3 }"


def pair_links(n):
    """Yield (peer, link_idx, local_port, local_ip, peer_ip, shunt_local, shunt_peer)."""
    for (a, b), links in LINKS.items():
        if n not in (a, b):
            continue
        peer = b if n == a else a
        for idx, (pa, pb) in enumerate(links, start=1):
            port = pa if n == a else pb
            lo, hi = f"10.{a}{b}.{idx}.0", f"10.{a}{b}.{idx}.1"
            local_ip, peer_ip = (lo, hi) if n == a else (hi, lo)
            slo, shi = f"10.1{a}{b}.{idx}.0", f"10.1{a}{b}.{idx}.1"
            s_local, s_peer = (slo, shi) if n == a else (shi, slo)
            yield peer, idx, port, local_ip, peer_ip, s_local, s_peer


def segw(n):
    p = SEGW[n]
    links = list(pair_links(n))
    peers = sorted({l[0] for l in links})
    ports = sorted({l[2] for l in links})

    port_cfg = "\n".join(
        f"    port {pt} {{ admin-state enable ethernet {{ mode hybrid encap-type dot1q }} }}" for pt in ports
    )

    if p["role"] == "active":
        isa = """    isa {
        tunnel-group 1 {
            admin-state enable
            isa-scale-mode tunnel-limit-2k
            ipsec-responder-only true
            multi-active {
                active-isa-number 1
                isa 1/2 { }
            }
        }
    }"""
    else:
        isa = """    isa {
        tunnel-member-pool "pool1" {
            isa 1/2 { }
        }
        tunnel-group 1 {
            admin-state enable
            isa-scale-mode tunnel-limit-2k
            ipsec-responder-only true
            multi-active {
                active-isa-number 1
                member-pool "pool1"
            }
        }
    }"""

    base_if = []
    ospf_if = []
    for peer, idx, port, lip, _pip, _sl, _sp in links:
        name = f"to-seg{peer}-{'ab'[idx - 1]}"
        base_if.append(
            f'        interface "{name}" {{ port {port}:1 ipv4 {{ primary {{ address {lip} prefix-length 31 }} {BFD} }} }}'
        )
        ospf_if.append(
            f'                interface "{name}" {{ interface-type point-to-point bfd-liveness {{ }} }}'
        )

    shunt_pub_if, shunt_pub_prof = [], []
    shunt_priv_if, shunt_priv_prof, vprn_shunt_if = [], [], []
    for peer, idx, port, lip, pip, sl, sp in links:
        if idx != 1:
            continue
        shunt_pub_if.append(
            f'            multi-chassis-shunt-interface "to-seg{peer}-a" {{ next-hop {{ address {pip} }} }}'
        )
        shunt_pub_prof.append(
            f'                peer 10.0.0.{peer} {{ multi-chassis-shunt-interface "to-seg{peer}-a" }}'
        )
        shunt_priv_if.append(
            f'            multi-chassis-shunt-interface "shunt-seg{peer}" {{ next-hop {{ address {sp} }} }}'
        )
        shunt_priv_prof.append(
            f'                peer 10.0.0.{peer} {{ multi-chassis-shunt-interface "shunt-seg{peer}" }}'
        )
        vprn_shunt_if.append(
            f'        interface "shunt-seg{peer}" {{ sap {port}:3 {{ }} ipv4 {{ primary {{ address {sl} prefix-length 31 }} }} }}'
        )

    mc_peers = []
    for peer in peers:
        mc_peers.append(f"""            peer 10.0.0.{peer} {{
                admin-state enable
                peer-name "seg{peer}"
                sync {{
                    admin-state enable
                    ipsec true
                }}
                mc-ipsec {{
                    bfd-liveness true
                    domain 1 {{ admin-state enable }}
                }}
            }}""")

    nl = "\n"
    return f"""configure {{
{port_cfg}
    port 1/1/9 {{ admin-state enable ethernet {{ mode network }} }}
    port 1/1/10 {{ admin-state enable ethernet {{ mode access }} }}
{isa}
    ipsec {{
        ike-transform 1 {{
            dh-group group-14
            ike-auth-algorithm sha-256
            ike-encryption-algorithm aes-128
            isakmp-lifetime 172800
        }}
        ipsec-transform 1 {{
            esp-auth-algorithm sha-256
            esp-encryption-algorithm aes-128
            ipsec-lifetime 7200
        }}
        ike-policy 1 {{
            ike-transform [1]
            ike-version-2 {{ auth-method psk }}
            dpd {{ interval 300 max-retries 3 reply-only true }}
        }}
        tunnel-template 1 {{
            ipsec-transform [1]
            sp-reverse-route use-security-policy
        }}
    }}
    redundancy {{
        multi-chassis {{
            ipsec-domain 1 {{
                admin-state enable
                designated-role {p["role"]}
                priority {p["prio"]}
                tunnel-group 1
            }}
{nl.join(mc_peers)}
        }}
    }}
    policy-options {{
        policy-statement "accept-all" {{ default-action {{ action-type accept }} }}
        policy-statement "export-ipsec" {{
            entry 10 {{
                from {{ protocol {{ name [ipsec] }} state ipsec-master-with-peer }}
                action {{ action-type accept metric {{ set 100 }} }}
            }}
            entry 20 {{
                from {{ protocol {{ name [ipsec] }} state ipsec-master-without-peer }}
                action {{ action-type accept metric {{ set 200 }} }}
            }}
            entry 30 {{
                from {{ protocol {{ name [ipsec] }} state ipsec-non-master }}
                action {{ action-type accept metric {{ set 1000 }} }}
            }}
            default-action {{ action-type reject }}
        }}
    }}
    router "Base" {{
        autonomous-system {SEGW_AS}
        router-id 10.0.0.{n}
        interface "system" {{ ipv4 {{ primary {{ address 10.0.0.{n} prefix-length 32 }} {BFD} }} }}
{nl.join(base_if)}
        interface "to-core" {{ port 1/1/9 ipv4 {{ primary {{ address 172.31.{n}.1 prefix-length 31 }} {BFD} }} }}
        ospf 0 {{
            admin-state enable
            area 0.0.0.0 {{
                interface "system" {{ passive true }}
{nl.join(ospf_if)}
            }}
        }}
        bgp {{
            group "core" {{
                peer-as {CORE_AS}
                bfd-liveness true
                import {{ policy ["accept-all"] }}
                export {{ policy ["export-ipsec"] }}
            }}
            neighbor "172.31.{n}.0" {{ group "core" }}
        }}
        ipsec {{
{nl.join(shunt_pub_if)}
            multi-chassis-shunting-profile "shunt-pub" {{
{nl.join(shunt_pub_prof)}
            }}
        }}
    }}
    service {{
        vprn "mobile" {{
            admin-state enable
            service-id 100
            customer "1"
            autonomous-system {SEGW_AS}
            ipsec {{
{nl.join(shunt_priv_if)}
                multi-chassis-shunting-profile "shunt-priv" {{
{nl.join(shunt_priv_prof)}
                }}
            }}
            interface "priv" {{
                tunnel true
                multi-chassis-shunting-profile "shunt-priv"
                sap tunnel-1.private:1 {{ }}
            }}
            interface "to-core" {{ sap 1/1/10 {{ }} ipv4 {{ primary {{ address 172.30.{n}.1 prefix-length 31 }} {BFD} }} }}
{nl.join(vprn_shunt_if)}
            bgp {{
                group "core" {{
                    peer-as {CORE_AS}
                    bfd-liveness true
                    import {{ policy ["accept-all"] }}
                    export {{ policy ["export-ipsec"] }}
                }}
                neighbor "172.30.{n}.0" {{ group "core" }}
            }}
        }}
        ies "public" {{
            admin-state enable
            service-id 10
            customer "1"
            interface "pub" {{
                multi-chassis-shunting-profile "shunt-pub"
                ipv4 {{ primary {{ address 198.51.100.254 prefix-length 24 }} }}
                sap tunnel-1.public:1 {{
                    ipsec-gateway "enb-gw" {{
                        admin-state enable
                        default-tunnel-template 1
                        ike-policy 1
                        pre-shared-key "{PSK}"
                        default-secure-service {{ service-name "mobile" interface "priv" }}
                        local {{ gateway-address {GW_ADDR} }}
                    }}
                }}
            }}
        }}
    }}
}}
"""


def ipmpls():
    pub = {1: "1/1/c1", 2: "1/1/c3", 3: "1/1/c5"}
    priv = {1: "1/1/c2", 2: "1/1/c4", 3: "1/1/c6"}
    edge = {"enb1": "1/2/c1", "enb2": "1/2/c2", "mme": "1/2/c3"}
    lines = ["configure {"]
    for c in list(pub.values()) + list(priv.values()) + list(edge.values()):
        lines.append(f"    port {c} {{ admin-state enable connector {{ breakout c1-100g }} }}")
    for c in list(pub.values()) + [edge["enb1"], edge["enb2"]]:
        lines.append(f"    port {c}/1 {{ admin-state enable ethernet {{ mode network }} }}")
    for c in list(priv.values()) + [edge["mme"]]:
        lines.append(f"    port {c}/1 {{ admin-state enable ethernet {{ mode access }} }}")
    lines.append(f"""    policy-options {{
        policy-statement "accept-all" {{ default-action {{ action-type accept }} }}
        policy-statement "export-direct" {{
            entry 10 {{ from {{ protocol {{ name [direct] }} }} action {{ action-type accept }} }}
            default-action {{ action-type reject }}
        }}
    }}
    router "Base" {{
        autonomous-system {CORE_AS}
        router-id 10.0.0.100
        interface "system" {{ ipv4 {{ primary {{ address 10.0.0.100 prefix-length 32 }} }} }}""")
    for n, c in pub.items():
        lines.append(
            f'        interface "to-seg{n}" {{ port {c}/1 ipv4 {{ primary {{ address 172.31.{n}.0 prefix-length 31 }} {BFD} }} }}'
        )
    lines.append(f'        interface "to-enb1" {{ port {edge["enb1"]}/1 ipv4 {{ primary {{ address 100.64.1.1 prefix-length 24 }} }} }}')
    lines.append(f'        interface "to-enb2" {{ port {edge["enb2"]}/1 ipv4 {{ primary {{ address 100.64.2.1 prefix-length 24 }} }} }}')
    lines.append(f"""        bgp {{
            group "segw" {{
                peer-as {SEGW_AS}
                bfd-liveness true
                import {{ policy ["accept-all"] }}
                export {{ policy ["export-direct"] }}
            }}""")
    for n in pub:
        lines.append(f'            neighbor "172.31.{n}.1" {{ group "segw" }}')
    lines.append("""        }
    }
    service {
        vprn "mobile" {
            admin-state enable
            service-id 100
            customer "1"
            autonomous-system %d""" % CORE_AS)
    for n, c in priv.items():
        lines.append(
            f'            interface "to-seg{n}" {{ sap {c}/1 {{ }} ipv4 {{ primary {{ address 172.30.{n}.0 prefix-length 31 }} {BFD} }} }}'
        )
    lines.append(f'            interface "to-mme" {{ sap {edge["mme"]}/1 {{ }} ipv4 {{ primary {{ address 10.200.0.1 prefix-length 24 }} }} }}')
    lines.append(f"""            bgp {{
                group "segw" {{
                    peer-as {SEGW_AS}
                    bfd-liveness true
                    import {{ policy ["accept-all"] }}
                    export {{ policy ["export-direct"] }}
                }}""")
    for n in priv:
        lines.append(f'                neighbor "172.30.{n}.1" {{ group "segw" }}')
    lines.append("""            }
        }
    }
}
""")
    return "\n".join(lines)


def swanctl(n):
    return f"""connections {{
    segw {{
        version = 2
        local_addrs = 100.64.{n}.2
        remote_addrs = {GW_ADDR}
        proposals = aes128-sha256-modp2048
        rekey_time = 86400s
        dpd_delay = 60s
        keyingtries = 0
        local {{
            auth = psk
            id = enb{n}
        }}
        remote {{
            auth = psk
        }}
        children {{
            s1u {{
                local_ts = 10.100.{n}.1/32
                remote_ts = 10.200.0.0/24
                esp_proposals = aes128-sha256
                rekey_time = 3600s
                start_action = start
                dpd_action = restart
                close_action = start
            }}
        }}
    }}
}}
secrets {{
    ike-segw {{
        secret = "{PSK}"
    }}
}}
"""


def main():
    OUT.mkdir(exist_ok=True)
    for n in SEGW:
        (OUT / f"seg{n}.partial.cfg").write_text(segw(n))
    (OUT / "ipmpls.partial.cfg").write_text(ipmpls())
    for n in (1, 2):
        d = OUT / f"enb{n}"
        d.mkdir(exist_ok=True)
        (d / "swanctl.conf").write_text(swanctl(n))
    print("configs written to", OUT)


if __name__ == "__main__":
    main()
