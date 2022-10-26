#!/bin/sh

set -euo

mkdir -pv /home/vagrant/test
cd /home/vagrant/test

fallocate -l 15GiB nilfs2.bin
mkfs -t nilfs2 nilfs2.bin
mkdir -p /mnt
mount -t nilfs2 nilfs2.bin /mnt

df | grep "/dev/loop0" >> df_before.txt
bonnie++ -d /mnt -s 1G -n 15 -m NILFS2 -b -u root -q >> out.csv
df | grep "/dev/loop0" >> df_after.txt

mv out.csv /vagrant/
mv *.txt /vagrant/

umount /mnt
rm nilfs2.bin
