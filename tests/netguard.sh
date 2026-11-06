#!/bin/bash
# Run on a Linux CI runner using sudo unshare --net -- bash tests/netguard.sh.
set -eu
if [[ $(readlink /proc/self/ns/net) == "$(readlink /proc/1/ns/net)" ]]; then
    echo "This test requires a private network namespace." >&2
    exit 1
fi

# Load the shipped rule functions without starting the Android service loop.
host_path=$PATH
guard=package/svc/netguard.sh
grep -qx 'if ! can_admin; then' "$guard"
source <(sed '/^if ! can_admin; then/,$d' "$guard")
export PATH=$host_path

for tool in iptables ip6tables; do
    "$tool" -N adb_fixture
    "$tool" -A adb_fixture -p tcp --dport 5555 -j DROP
    "$tool" -A INPUT -j adb_fixture
done
before4=$(iptables -S)
before6=$(ip6tables -S)

check_uid() {
    local uid=$1 tool rules
    for tool in iptables ip6tables; do
        "$tool" -C OUTPUT -j smarttube_net
        rules=$("$tool" -S smarttube_net)
        [[ $(grep -c '^-A ' <<< "$rules") == 8 ]]
        [[ $(sed -n '2p' <<< "$rules") == *"! --uid-owner $uid -j RETURN" ]]
        for iface in lo wlan+ bnep+ bt-pan+ usb+ rndis+; do
            "$tool" -C smarttube_net -o "$iface" -j RETURN
        done
        [[ ${rules##*$'\n'} == "-A smarttube_net -j REJECT"* ||
           ${rules##*$'\n'} == "-A smarttube_net -j DROP" ]]
    done
}

for uid in 10201 10202; do
    apply "$uid" || exit 1
    applied "$uid"
    check_uid "$uid"
done

sh package/scripts/preun.sh
[[ $(iptables -S) == "$before4" ]]
[[ $(ip6tables -S) == "$before6" ]]
