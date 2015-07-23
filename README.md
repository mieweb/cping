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

## Install ##
git clone this project

### Linux ###
The main folder, run make.

### Mac OSX ###
cd osx; make
