#!/usr/bin/env python3
import subprocess
import socket
import time
import sys
import itertools

# Configuration – adjust these values for your environment:
# Candidate IP addresses to check
LOCAL_IP = ""
TAILSCALE_IPV4 = ""
TAILSCALE_IPV6 = ""
CHECK_IPS = [LOCAL_IP, TAILSCALE_IPV4, TAILSCALE_IPV6]

BROADCAST = ""      # Broadcast address for WoL
MAC_ADDR = ""    # Target PC's MAC address
ATTEMPTS = 5                   # Maximum number of scan cycles
SLEEP_BETWEEN_ATTEMPTS = 2     # Seconds to wait between scan cycles
PING_TIMEOUT = 2               # Ping timeout in seconds

def ping_ip(ip):
    """
    Ping the given IP.
    Uses 'ping' for IPv4 and 'ping -6' for IPv6.
    Returns True if the ping succeeds.
    """
    if ":" in ip:
        # IPv6 address
        cmd = ["ping", "-6", "-c", "1", "-W", str(PING_TIMEOUT), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(PING_TIMEOUT), ip]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except Exception:
        return False

def scan_ips():
    """
    Returns a list of candidate IPs from CHECK_IPS that respond to ping.
    """
    live = []
    for ip in CHECK_IPS:
        if ping_ip(ip):
            live.append(ip)
    return live

def send_wol(mac, broadcast):
    """
    Sends a Wake-on-LAN magic packet for the given MAC address.
    """
    mac_clean = mac.replace(":", "")
    packet = bytes.fromhex("FF" * 6 + mac_clean * 16)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(packet, (broadcast, 9))
    sock.close()

def throbber(duration=1.0):
    """
    Displays a continuously updating ASCII throbber (fluid animation)
    on the same line for the specified duration.
    """
    frames = ["┌──┐", "│◐ │", "│ ─┘", "│◑ │"]
    cycle_frames = itertools.cycle(frames)
    end_time = time.time() + duration
    while time.time() < end_time:
        frame = next(cycle_frames)
        sys.stdout.write("\rScanning... " + frame)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\rScanning... " + frame)
    sys.stdout.flush()

def main():
    live_ips = scan_ips()
    if live_ips:
        print("\nPC is already on. Responding IPs:", ", ".join(live_ips))
        return

    print("PC appears to be off. Sending Wake-on-LAN packet...")
    send_wol(MAC_ADDR, BROADCAST)
    print("Magic packet sent. Waiting for the PC to wake up...")

    for _ in range(ATTEMPTS):
        throbber(duration=1.0)
        live_ips = scan_ips()
        if live_ips:
            print("\nPC is now online. Responding IPs:", ", ".join(live_ips))
            return
        time.sleep(SLEEP_BETWEEN_ATTEMPTS)
    print("\nPC did not wake up after {} scan cycles.".format(ATTEMPTS))

if __name__ == "__main__":
    main()
