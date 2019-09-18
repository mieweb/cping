# $Id: Makefile,v 1.2 2007/06/03 17:50:16 jasone Exp $

# Path to parent kernel include files directory
LIBC_INCLUDE=/usr/include

DEFINES= 

#options if you have a bind>=4.9.4 libresolv (or, maybe, glibc)
LDLIBS=-lresolv
ADDLIB=

#options if you compile with libc5, and without a bind>=4.9.4 libresolv
# NOT AVAILABLE. Please, use libresolv.

CC=gcc -static
# What a pity, all new gccs are buggy and -Werror does not work. Sigh.
#CCOPT=-D_GNU_SOURCE -O2 -Wstrict-prototypes -Wall -g -Werror
CCOPT=-D_GNU_SOURCE -O2 -Wstrict-prototypes -Wall -g
CFLAGS=$(CCOPT) $(GLIBCFIX) $(DEFINES) 

IPV4_TARGETS=cping
TARGETS=$(IPV4_TARGETS)

LASTTAG:=`git-describe HEAD | sed -e 's/-.*//'`
TAG:=`date +s%Y%m%d`

all: $(TARGETS)


cping: cping.o cping_common.o
cping.o cping_common.o: cping_common.h

check-kernel:
ifeq ($(KERNEL_INCLUDE),)
	@echo "Please, set correct KERNEL_INCLUDE"; false
else
	@set -e; \
	if [ ! -r $(KERNEL_INCLUDE)/linux/autoconf.h ]; then \
		echo "Please, set correct KERNEL_INCLUDE"; false; fi
endif

modules: check-kernel
	$(MAKE) KERNEL_INCLUDE=$(KERNEL_INCLUDE) -C Modules

clean:
	@rm -f *.o $(TARGETS)
