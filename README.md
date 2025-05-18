cping
=====

A cooler version of ping that has a -F threshold in milliseconds option.  With -F specified, only 
packets that miss the threshold are printed.  Also, if the target host goes down, the duration of the downtime
is printed in summary.  Also multiple cpings can be run in the background (ie: ```cping -F 10 host &```) and the output will show which host missed a ping threshold.

```
$ cping -F 30 google.com

You asked for only failed pings to be displayed.

PING google.com (173.194.46.69) 56(84) bytes of data.
64 bytes from ord08s11-in-f5.1e100.net (173.194.46.69): icmp_seq=14 ttl=53 time=32.0 ms -- TO > thresh 30 ms Mar 28 23:46:31 2014
64 bytes from ord08s11-in-f5.1e100.net (173.194.46.69): icmp_seq=21 ttl=53 time=31.3 ms -- TO > thresh 30 ms Mar 28 23:46:38 2014
64 bytes from ord08s11-in-f5.1e100.net (173.194.46.69): icmp_seq=23 ttl=53 time=41.3 ms -- TO > thresh 30 ms Mar 28 23:46:40 2014
64 bytes from ord08s11-in-f5.1e100.net (173.194.46.69): icmp_seq=24 ttl=53 time=31.5 ms -- TO > thresh 30 ms Mar 28 23:46:41 2014

--- google.com ping statistics ---
26 packets transmitted, 25 received, 3% packet loss, time 25012ms
rtt min/avg/max/mdev = 23.964/27.200/41.342/3.688 ms

```

```
$ cping -F 30 192.168.1.99

You asked for only failed pings to be displayed.

PING 192.168.1.99 (192.168.1.99) 56(84) bytes of data.
Mar 28 23:47:43 2014 Missing pings.  Down for 2.998395 secs
Mar 28 23:47:48 2014 Missing pings.  Down for 8.324291 secs
--- 192.168.1.99 ping statistics ---
12 packets transmitted, 0 received, +9 errors, 100% packet loss, time 10994ms
```

## Implementations ##

cping is available in both Python and C implementations:

### Python Implementation ###
The Python version (`cping.py`) requires Python 3 and provides platform-independent functionality. It's easy to use without compilation:

```
sudo python3 cping.py -F 30 google.com
```

You can also download and run the Python version directly without cloning the repository:

```
curl -o cping.py https://raw.githubusercontent.com/mieweb/cping/master/cping.py
sudo python3 ./cping.py -F 30 google.com
```

Or run it directly in a single command:

```
sudo python3 <(curl -s https://raw.githubusercontent.com/mieweb/cping/master/cping.py) -F 30 google.com
```

**Note:** Root privileges (sudo) are required to create ICMP sockets used for ping functionality.

### C Implementation ###
The C implementation offers better performance and is compiled for specific platforms:

```
sudo cping -F 30 google.com
```

**Note:** Root privileges (sudo) are required to create ICMP sockets used for ping functionality.

## Install ##
git clone this project

```
git clone https://github.com/mieweb/cping.git
cd cping
```

### Linux ###
In the main folder, run make:

```
make
```

### Mac OSX ###
For macOS, use the OSX-specific version:

```
cd osx
make
```

## Requirements ##

### Python Version ###
- Python 3.x
- Root/sudo privileges for ICMP socket access

### C Version ###
- Linux: gcc compiler, standard C libraries, root/sudo privileges
- macOS: Xcode command line tools, root/sudo privileges
