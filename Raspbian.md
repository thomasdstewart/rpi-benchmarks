# Raspberry Pi 4 Benchmarks
# Table of contents
   * [Background](#background)
   * [Aim](#aim)
   * [Method](#method)
      * [Install System](#install-system)
      * [System Size](#system-size)
      * [Copying System to Media](#copying-system-to-media)
      * [Software Versions](#software-versions)
      * [Benchmark Scripts](#benchmark-scripts)
      * [Running Method](#running-method)
      * [Raspberry Pi 4 Firmware](#raspberry-pi-4-firmware)
      * [Running Kernel Version and Memory](#running-kernel-version-and-memory)
      * [Cooling](#cooling)
   * [Results](#results)
      * [Raw](#raw)
      * [Averaged](#averaged)
      * [GCC Differences](#gcc differences)
   * [Conclusion](#conclusion)
   * [Addendum](#addendum)

## Background
After completing the Debian based armhr/armv7l or Debian aarch64/arm64 (ie 32bit vs 64bit) benchmarks I mentioned that I repeated the test in an ad-hoc manor on a Rasbian system and they ran far faster, in the order of half the run time.

## Aim
Find out if Debian armhf/armv7l (32bit) or Rasbian armhf/armv7l (32bit) performs better on Raspberry Pi 4 with a single external USB root filesystem (WD 5TB Elements Portable External Hard Drive, USB 3.0 https://www.amazon.co.uk/gp/product/B07X41PWTY/).

## Install System
The mechanism to build the raspberry pi disk images were copy and pasting shell commands. The following commands were used to create both images, copying and pasting several lines at a time and checking the output was expected.

```
sudo rm -r -f deb ras
pkg="aptitude,bc,binutils,bison,bind9-host,build-essential,curl,debconf-utils,dnsutils,fake-hwclock,file,flex,git,less,libssl-dev,locales,netcat-traditional,ntp,ntpdate,pv,screen,sudo,task-ssh-server,tcpdump,telnet,vim-gtk,wget"
sudo debootstrap --arch armhf --include=$pkg buster deb http://deb.debian.org/debian 

v=1.20190925+1-1
for p in raspberrypi-kernel_${v}_armhf.deb raspberrypi-bootloader_${v}_armhf.deb; do
        sudo chroot deb wget http://archive.raspberrypi.org/debian/pool/main/r/raspberrypi-firmware/$p
        sudo chroot deb dpkg -i $p 
        sudo rm deb/$p
done

wget https://downloads.raspberrypi.org/raspbian_lite_latest
unzip raspbian_lite_latest
sudo modprobe loop max_part=20
sudo losetup -P /dev/loop0 2020-02-13-raspbian-buster-lite.img
sudo rm -r -f raw
mkdir t ras
sudo mount /dev/loop0p2 t
sudo mount /dev/loop0p1 t/boot
sudo rsync -vaHAXSP ./t/. ./ras/.
sudo umount t/boot t
rmdir t
rm 2020-02-13-raspbian-buster-lite.img raspbian_lite_latest

sudo cp /usr/bin/qemu-arm-static deb/usr/bin
sudo cp /usr/bin/qemu-arm-static ras/usr/bin

echo deb | sudo tee deb/etc/hostname
echo ras | sudo tee ras/etc/hostname

echo "console=tty1 root=/dev/sda1 rootfstype=ext4 rootflags=commit=100,discard,data=writeback elevator=deadline fsck.repair=yes rootwait" | sudo tee deb/boot/cmdline.txt
sudo cp deb/boot/cmdline.txt ras/boot/cmdline.txt

cat ras/boot/config.txt  | egrep -v "^#|^$" | sudo tee deb/boot/config.txt

cat << EOF | sudo tee deb/etc/fstab
/dev/sda1 / ext4 defaults,noatime,nodiratime,errors=remount-ro,commit=100,discard,data=writeback 0 1
/dev/mmcblk0p1 /boot vfat defaults,noatime,nodiratime 0 2 
EOF
sudo cp deb/etc/fstab ras/etc/fstab

cat << EOF | sudo tee deb/etc/apt/sources.list
deb     http://deb.debian.org/debian/       buster           main non-free contrib
#deb     http://deb.debian.org/debian/       bullseye           main non-free contrib
#deb     http://deb.debian.org/debian/       bullseye-updates   main non-free contrib
#deb     http://deb.debian.org/debian/       sid                main non-free contrib
#deb     http://deb.debian.org/debian/       experimental       main non-free contrib
#deb     http://security.debian.org/         bullseye-security  main non-free contrib
deb [arch=armhf] http://archive.raspberrypi.org/debian/ buster main
EOF

curl http://archive.raspberrypi.org/debian/raspberrypi.gpg.key | sudo tee deb/etc/apt/trusted.gpg.d/raspberrypi.asc
cat << EOF | sudo tee deb/etc/apt/preferences
Package: *
Pin: release testing
Pin-Priority: 800

Package: *
Pin: release unstable
Pin-Priority: 700

Package: *
Pin: release experimental
Pin-Priority: 600

Package: *
Pin: origin "archive.raspberrypi.org"
Pin-Priority: -100

Package: raspberrypi-bootloader raspberrypi-kernel
Pin: origin "archive.raspberrypi.org"
Pin-Priority: 1100

EOF

cat << EOF | sudo tee deb/etc/systemd/network/0-wired.network
[Match]
Name=e*

[Network]
DHCP=yes

[DHCP]
RouteMetric=10
ClientIdentifier=mac
EOF

sudo chroot deb systemctl enable ssh
sudo chroot ras systemctl enable ssh

sudo chroot deb systemctl enable systemd-networkd

echo "locales locales/default_environment_locale select en_GB.UTF-8" | sudo chroot deb debconf-set-selections
echo "locales locales/default_environment_locale select en_GB.UTF-8" | sudo chroot ras debconf-set-selections
echo "locales locales/locales_to_be_generated multiselect en_GB.UTF-8 UTF-8" | sudo chroot deb debconf-set-selections
echo "locales locales/locales_to_be_generated multiselect en_GB.UTF-8 UTF-8" | sudo chroot ras debconf-set-selections
sudo sed -i 's/^# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' deb/etc/locale.gen
sudo sed -i 's/^# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' ras/etc/locale.gen

sudo chroot deb dpkg-reconfigure --frontend=noninteractive locales
sudo chroot ras dpkg-reconfigure --frontend=noninteractive locales

sudo chroot deb adduser --gecos thomas pi
sudo chroot ras passwd pi

sudo cp -a ras/etc/sudoers.d/0* deb/etc/sudoers.d/

sudo chroot deb apt-get update
sudo chroot ras apt-get update

sudo chroot deb apt-get upgrade
sudo chroot ras apt-get upgrade

sudo chroot ras apt-get -y install $(echo $pkg | sed 's/,/ /g')

sudo chroot deb dpkg -l | grep ^ii | awk '{print $2}' > p
sudo chroot ras dpkg -l | grep ^ii | awk '{print $2}' >> p

sudo chroot ras apt-get install $(cat p | sort | uniq | xargs)
sudo chroot deb apt-get install $(cat p | sort | uniq | egrep -v "gcc-4.9-base|gcc-5-base|gcc-6-base|libboost-iostreams1.58.0|libreadline6|libsigc|libudev0|raspbian-archive-keyring" | xargs)
rm p

sudo chroot deb dpkg -l | grep ^ii | awk '{print $2 " " $3}' > dpkg-l.deb.txt.p
sudo chroot ras dpkg -l | grep ^ii | awk '{print $2 " " $3}' > dpkg-l.ras.txt.p

sudo chroot deb apt-get clean
sudo chroot ras apt-get clean

sudo chroot deb su -c "wget https://github.com/torvalds/linux/archive/v5.4.tar.gz" - pi
sudo cp deb/home/pi/v5.4.tar.gz ras/home/pi/v5.4.tar.gz
sudo chroot deb su -c "tar xf v5.4.tar.gz" - pi &
sudo chroot ras su -c "tar xf v5.4.tar.gz" - pi &
wait

cat << EOF | sudo tee deb/home/pi/linux-5.4/run.sh
#!/bin/bash -x
export KBUILD_BUILD_TIMESTAMP="16 Dec 2019 00:00:00"
export KBUILD_BUILD_HOST=pi
make mrproper
make defconfig
(time make -j 4 zImage; md5sum arch/arm/boot/zImage 1>&2) 2> result.\$(date +%s)
EOF
sudo cp deb/home/pi/linux-5.4/run.sh ras/home/pi/linux-5.4/run.sh

sudo chmod +x deb/home/pi/linux-5.4/run.sh ras/home/pi/linux-5.4/run.sh
```

### System Size
Rasbian is 1% larger on disk than Debian, this is probably due to the extra package installed but not avaliable in Debian.
```
$ sudo du -sh deb ras
2.5G	deb
2.5G	ras
$ sudo du -sk deb ras
2577444	deb
2610016	ras
```

### Copying System to Media
Both SD card and USB disk had new parition tables created and new blank empty filesystems created with apropreate lables so they would mount in consistant places. The following commands were used to copy the system to the media for the Debian test:
```

sudo rm -r -f /media/thomas/root/* /media/thomas/boot/*

sudo rsync -cax --delete ./deb/. /media/thomas/root/.
sudo rsync -crptx --delete ./deb/boot/. /media/thomas/boot/.
sudo umount /media/thomas/boot /media/thomas/root
```

Later to update to the 64 bit system the following commands were used (note that the Linux src will remain on the same inodes on disk):
```
sudo rsync -cax --delete ./ras/. /media/thomas/root/.
sudo rsync -crptx --delete ./ras/boot/. /media/thomas/boot/.
sudo umount /media/thomas/boot /media/thomas/root
```

### Software Versions
The Debian systems ran buster and all software was up to date at the time of the test which was just after 2th February 2020. The versions of all the software were recorded via "dpkg -l" and saved into [dpkg-l.deb.txt](dpkg-l.deb.txt) and [dpkg-l.ras.txt](dpkg-l.ras.txt). The git ref for the Linux repo is 219d543 which is tagged v5.4.

### Benchmark Scripts
The benchmark scripts are embedded into the above build script, however to aid readability the first step is to download the source from https://github.com/torvalds/linux/archive/v5.4.tar.gz and extract it. Each system has a run.sh script created. The first step is to set the build timestamp and host, so that the end images will be the same, thanks to reproducible builds this works very well. The next step is to completely clean the source with make mrpropper. The last step is to build zImage, run a md5sum to verify the image produced is the same and to record the time taken.

The run.sh script looks like:
```
#!/bin/bash -x
export KBUILD_BUILD_TIMESTAMP="16 Dec 2019 00:00:00"
export KBUILD_BUILD_HOST=pi
make mrproper
make defconfig
(time make -j 4 zImage; md5sum arch/arm/boot/zImage 1>&2) 2> result.$(date +%s)
```

### Running Method
Each benchmark was repeated 10 times, the method to run a benchmark was to boot the Rapsberry Pi, ssh to it and run the following:
```
screen
cd linux-5.4/
for n in $(seq 10); do ./run.sh; done

### Raspberry Pi 4 Firmware
The firmware of the Rasbperry Pi 4 was updated by running a Rasbian image. No firmware updates were performed after the 32bit vs 64bit tests. The firmware at the time was the following: 
```
root@raspberrypi:~# rpi-eeprom-update
BOOTLOADER: up-to-date
CURRENT: Tue 10 Sep 10:41:50 UTC 2019 (1568112110)
 LATEST: Tue 10 Sep 10:41:50 UTC 2019 (1568112110)
VL805: up-to-date
CURRENT: 000137ab
 LATEST: 000137ab
root@raspberrypi:~#

### Running Kernel Version and Memory
Once booted each system had "uname -a" and "free -h" run. On the Debian it looked like:
```
pi@deb:~$  uname -a
Linux deb 4.19.97-v7l+ #1294 SMP Thu Jan 30 13:21:14 GMT 2020 armv7l GNU/Linux
pi@deb:~$
pi@deb:~$ free -h
              total        used        free      shared  buff/cache   available
Mem:          3.8Gi       181Mi       3.1Gi        16Mi       548Mi       3.5Gi
Swap:         2.0Gi          0B       2.0Gi
pi@deb:~$ 
```

On Rasbian it looked like:
```
pi@ras:~ $ uname -a
Linux ras 4.19.97-v7l+ #1294 SMP Thu Jan 30 13:21:14 GMT 2020 armv7l GNU/Linux
pi@ras:~ $ 
pi@ras:~ $ free -h
              total        used        free      shared  buff/cache   available
Mem:          3.8Gi       110Mi       2.9Gi        16Mi       800Mi       3.6Gi
Swap:          99Mi          0B        99Mi
pi@ras:~ $
```

## Cooling
For the duration of these tests the ICE-Tower Raspberry Pi 4 CPU Cooler with fan.

## Results
The results were captured and stored in the [raw-results2.txt](raw-results2.txt]) file. The raw results have been extracted from raw-results.txt and shown below.

### Raw

 1. ICE-Tower Raspberry Pi 4 CPU Cooler with fan Debian data: 23m10.613s 23m6.807s 23m5.372s 23m5.337s 23m6.170s 23m6.107s 23m7.098s 23m7.211s 23m7.168s 23m4.263s
 1. ICE-Tower Raspberry Pi 4 CPU Cooler with fan Rasbian data: 20m34.594s 20m31.159s 20m29.733s 20m30.855s 20m30.834s 20m30.456s 20m31.374s 20m29.973s 20m28.104s 20m30.161s

### Averaged

| Test | Average time taken to complete (minutes) |
| ---  | --- |
| ICE-Tower Raspberry Pi 4 CPU Cooler with fan Debian  | 23.11 |
| ICE-Tower Raspberry Pi 4 CPU Cooler with fan Rasbian | 20.51 |

### GCC Differences
The GCC compiler has slightly different compiler options. These can be showed with the '-v' option. Looking at the options the following can be used to compare them:

```
sudo chroot deb gcc -v 2>&1 | sed 's/ /\n/g' | sort | grep -- -- > deb.gcc.txt
sudo chroot ras gcc -v 2>&1 | sed 's/ /\n/g' | sort | grep -- -- > ras.gcc.txt
```

Debian has:
 . --enable-default-pie
 . --with-arch=armv7-a
 . --with-fpu=vfpv3-d16
 . --with-mode=thumb

Rasbian has:
 . (no mention of pie)
 . --with-arch=armv6
 . --with-fpu=vfp
 . (no mention of mode)

Looking at a simple hellow world C program:
```
#include <stdio.h>
int main(void) {
    printf("Hello World");
}
```

And compiling it with:
```
$ sudo chroot deb gcc -o hello hello.c
$ sudo chroot ras gcc -o hello hello.c
```

Does result in different binaries:
```
$ file deb/hello ras/hello
deb/hello: ELF 32-bit LSB shared object, ARM, EABI5 version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-armhf.so.3, for GNU/Linux 3.2.0, BuildID[sha1]=722e2d6f0df08c60bb0d492bdaf83d279b88bc38, not stripped
ras/hello: ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-armhf.so.3, for GNU/Linux 3.2.0, BuildID[sha1]=b3570c55fcf2b171afbf215d3de416331e5fe4a6, not stripped
```

Looking at the assembly generated for Debian:
```
$ objdump -d --start-address=0x50c --stop-address=0x520 deb/hello 

deb/hello:     file format elf32-littlearm


Disassembly of section .text:

0000050c <main>:
 50c:	b580      	push	{r7, lr}
 50e:	af00      	add	r7, sp, #0
 510:	4b03      	ldr	r3, [pc, #12]	; (520 <main+0x14>)
 512:	447b      	add	r3, pc
 514:	4618      	mov	r0, r3
 516:	f7ff ef5a 	blx	3cc <printf@plt>
 51a:	2300      	movs	r3, #0
 51c:	4618      	mov	r0, r3
 51e:	bd80      	pop	{r7, pc}
```

And for Rasbian:
```
$ objdump -d --start-address=0x10408 --stop-address=0x10424 ras/hello

ras/hello:     file format elf32-littlearm


Disassembly of section .text:

00010408 <main>:
   10408:	e92d4800 	push	{fp, lr}
   1040c:	e28db004 	add	fp, sp, #4
   10410:	e59f000c 	ldr	r0, [pc, #12]	; 10424 <main+0x1c>
   10414:	ebffffb3 	bl	102e8 <printf@plt>
   10418:	e3a03000 	mov	r3, #0
   1041c:	e1a00003 	mov	r0, r3
   10420:	e8bd8800 	pop	{fp, pc}
```

## Conclusion
 * Debian apears to be 13% faster than Rasbian
 * Something drastic has changed between the previous test and this one as the previous best test was 85% slower. Either kernel version changes or other version changes.

## Addendum]
Repeating tests...
