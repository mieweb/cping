#!/usr/bin/env python3

import os
import socket
import struct
import time
import select
import argparse
import signal
import sys
from datetime import datetime

ICMP_ECHO_REQUEST = 8
PING_INTERVAL = 1.0  # Default interval in seconds
DEFAULT_PAYLOAD_SIZE = 56  # Standard ping default payload size

class HostState:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
        self.seq = 1
        self.last_sent = 0
        self.failure_state = False
        self.failure_since = 0  # Add this to track when failure began
        self.status_line_active = False  # Add this to track if we're showing a status line

def checksum(data: bytes) -> int:
    """
    Compute the Internet Checksum of the supplied data.
    """
    if len(data) % 2:
        data += b'\x00'  # Pad with zero byte if not even

    total = 0
    for i in range(0, len(data), 2):
        word = data[i] << 8 | data[i + 1]
        total += word
        total &= 0xffffffff  # Keep in 32 bits

    # Fold 32-bit sum to 16 bits
    while total >> 16:
        total = (total & 0xffff) + (total >> 16)

    return ~total & 0xffff

def create_packet(pid, seq, payload_size=56):
    """Create an ICMP echo request packet with the specified payload size."""
    # Make sure sequence number is in the right range (1-65535)
    seq = seq % 65536
    
    # Use network byte order (big-endian) for all values in the ICMP header
    header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, 0, pid, seq)
    
    # First 8 bytes are timestamp in 
    data = struct.pack('d', time.time())
    
    # Pad the rest with sequential bytes to reach desired payload size
    if payload_size > 8:
        pad_size = payload_size - 8
        data += bytes(i % 256 for i in range(pad_size))
        
    chksum = checksum(header + data)
    # Note the '!' format prefix for network byte order
    header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, chksum, pid, seq)
    
    return header + data


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    parser = argparse.ArgumentParser(description="Async multi-host ping monitor")
    parser.add_argument("-F", "--fail-threshold", type=int, default=100,
                        help="RTT threshold in ms to report alerts (default: 100)")
    parser.add_argument("-i", "--interval", type=float, default=1.0,
                        help="Ping interval in seconds (default: 1.0)")
    parser.add_argument("-s", "--size", type=int, default=DEFAULT_PAYLOAD_SIZE,
                        help=f"Payload size in bytes (default: {DEFAULT_PAYLOAD_SIZE})")
    parser.add_argument("--debug", action="store_true", help="Enable debug output for sending/receiving ICMP")
    parser.add_argument("hosts", nargs="+", help="List of hosts to ping")
    args = parser.parse_args()

    threshold = args.fail_threshold
    debug = args.debug
    hostnames = args.hosts
    ping_interval = args.interval  # Use the command line interval
    payload_size = args.size

    pid = os.getpid() & 0xFFFF
    hosts = {}

    try:
        for h in hostnames:
            ip = socket.gethostbyname(h)
            # Initialize each host with sequence number 1
            hosts[ip] = HostState(h, ip)
    except socket.gaierror as e:
        print(f"Error resolving host: {e}")
        return

    # Create a blocking socket for ICMP
    # Non-blocking mode seems to prevent ICMP packets from being sent
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    sock.setblocking(False)
    
    print(f"PID: {pid}, Monitoring hosts: {', '.join([f'{h.name}/{h.ip}' for h in hosts.values()])}")

    # Statistics tracking
    stats = {ip: {"sent": 0, "received": 0, "rtt_sum": 0, "min_rtt": float('inf'), "max_rtt": 0} 
             for ip in hosts}
    
    # Signal handler for clean exit
    def signal_handler(sig, frame):
        print("\n--- Ping statistics ---")
        for ip, host in hosts.items():
            host_stats = stats[ip]
            sent = host_stats["sent"]
            received = host_stats["received"]
            loss = 0 if sent == 0 else 100 - (received * 100 / sent)
            
            print(f"{host.name} ({ip}):")
            print(f"  {sent} packets transmitted, {received} received, {loss:.1f}% packet loss")
            
            if received > 0:
                avg_rtt = host_stats["rtt_sum"] / received
                print(f"  rtt min/avg/max = {host_stats['min_rtt']:.3f}/{avg_rtt:.3f}/{host_stats['max_rtt']:.3f} ms")
        
        print("\nExiting...")
        sys.exit(0)
    
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        now = time.monotonic()

        # Send pings
        for host in hosts.values():
            if now - host.last_sent >= ping_interval:  # Use the configured interval
                packet = create_packet(pid, host.seq, payload_size)
                try:
                    sent_bytes = sock.sendto(packet, (host.ip, 0))
                    if sent_bytes != len(packet):
                        print(f"Warning: Only sent {sent_bytes} of {len(packet)} bytes")
                    
#                    if debug:
#                        print(f"[DEBUG] Sending ICMP to {host.name}/{host.ip} seq={host.seq}, packet_size={len(packet)}")
                    host.last_sent = now
                    host.seq += 1
                    stats[host.ip]["sent"] += 1
                except Exception as e:
                    print(f"[{timestamp()}] [{host.name}/{host.ip}] Send failed: {e}")

        # Read replies
        readable, _, _ = select.select([sock], [], [], 0.1)
        if readable:
            try:
                packet, addr = sock.recvfrom(1024)
                recv_time = time.time()
                ip = addr[0]

                # Extract ICMP from dynamic offset
                ip_header_len = (packet[0] & 0x0F) * 4
                icmp_header = packet[ip_header_len:ip_header_len + 8]
                payload = packet[ip_header_len + 8:]

                # Use network byte order (big-endian) with '!' format prefix
                _type, code, chksum, recv_id, seq = struct.unpack("!bbHHh", icmp_header)

                # Consolidated debug output into a single line
                if debug:
                    host_status = f"monitored={ip in hosts}"
                    id_match = f"id_match={recv_id == pid}" if ip in hosts else "id_check=skipped"
                    payload_info = f"payload={len(payload)}B"
                    rtt_info = ""
                    if ip in hosts and recv_id == pid and len(payload) >= 8:
                        time_sent = struct.unpack("d", payload[:8])[0]
                        rtt = (recv_time - time_sent) * 1000  # ms
                        rtt_info = f", rtt={rtt:.2f}ms"
#                    print(f"[DEBUG {pid}] ICMP: src={ip}, type={_type}, code={code}, id={recv_id}, seq={seq}, {host_status}, {id_match}, {payload_info}{rtt_info}")

                if recv_id != pid:
#                    if debug:
 #                       print(f"[DEBUG {pid}] Skipping: id={recv_id} doesn't match pid={pid}")
                    continue

                # Check if the IP is in our monitored hosts
                if ip not in hosts:
                    if debug:
                        print(f"[DEBUG] Skipping: {ip} not in monitored hosts")
                    continue

                # Get the host state
                host = hosts[ip]

                if len(payload) >= 8:
                    time_sent = struct.unpack("d", payload[:8])[0]
                    rtt = (recv_time - time_sent) * 1000  # ms
                else:
                    if debug:
                        print(f"[DEBUG] Payload: too short ({len(payload)}B)")
                    rtt = None

                ts = timestamp()

                if rtt is not None:
                    # Update statistics
                    host_stats = stats[ip]
                    host_stats["received"] += 1
                    host_stats["rtt_sum"] += rtt
                    host_stats["min_rtt"] = min(host_stats["min_rtt"], rtt)
                    host_stats["max_rtt"] = max(host_stats["max_rtt"], rtt)
                    
                    output = f"[{ts}] [{host.name}/{host.ip}] icmp_seq={seq} time={rtt:.2f} ms"
                    if rtt > threshold:
                        if not host.failure_state:
                            print(f"{output} DOWN (threshold={threshold} ms)")
                            host.failure_state = True
                            host.failure_since = time.time()
                            host.status_line_active = True
                        else:
                            # Always show the status line, not just in debug mode
                            down_time = time.time() - host.failure_since
                            print(f"\r{output} Missing pings. Down for {down_time:.6f} secs", end="", flush=True)
                    else:
                        if host.failure_state:
                            # Clear the line with spaces before printing recovery message
                            if host.status_line_active:
                                print("\r" + " " * 100, end="", flush=True)  # Clear the current line
                            
                            # Calculate total downtime
                            total_downtime = time.time() - host.failure_since
                            
                            print(f"\r{output} UP (recovered<={threshold} ms, down for {total_downtime:.6f} secs)")
                            host.failure_state = False
                            host.status_line_active = False
                        elif debug:
                            print(output)
                else:
                    print(f"[{ts}] [{host.name}/{host.ip}] icmp_seq={seq} received (no RTT info)")
            except Exception as e:
                # Handle malformed packets or other errors and show line number
                print(f"[{timestamp()}] Receive error: {e}")

        time.sleep(0.01) # Sleep to prevent busy waiting

if __name__ == "__main__":
    main()
