#!/bin/bash

set -eu -o pipefail

ISO_PATH="/mnt/custom-iso/"
ISO_VERSION="CentOS-7-x86_64-Minimal-2003.iso"
CUSTOM_ISO_VERSION="cortx-custom.iso"
ISO_MOUNT_PATH="/mnt/custom-iso/test"
LOCAL_BOOT_PATH="/mnt/custom-iso/bootisoks"
KICKSTART_FILE="./kickstart_centos-7.8.2003.cfg"
CORTX_DEPS_PATH="/mnt/bigstorage/releases/cortx/third-party-deps/"
OS="centos"
OS_VERSION="centos-7.8.2003"

rm -rf /mnt/custom-iso/custom-packages/ && mkdir -p /mnt/custom-iso/custom-packages/ 

#Mount ISO locally
echo -e "-------------------------[ Mount CentOS-7-x86_64-Minimal-2003.iso ]----------------------------------------" 
mkdir -p $ISO_MOUNT_PATH && mount -o loop $ISO_PATH/$ISO_VERSION $ISO_MOUNT_PATH

#Install required packages 
echo -e "-------------------------[ Install required package ]------------------------------------------------------" 
yum install pykickstart createrepo genisoimage isomd5sum -y

#create local folder and copy ISO folders
rm -rf $LOCAL_BOOT_PATH && mkdir -p $LOCAL_BOOT_PATH
cp -r "$ISO_MOUNT_PATH"/* $LOCAL_BOOT_PATH

#umount ISO and remove folder
umount $ISO_MOUNT_PATH && rm $ISO_MOUNT_PATH -rf

#set permissions for local folder
chmod -R u+w $LOCAL_BOOT_PATH

#validate kickstart file
echo -e "-------------------------[ Validate kickstart file ]--------------------------------" 
ksvalidator $KICKSTART_FILE

#copy kickstart file and update isolinux.cfg
echo -e "-------------------------[ Update isolinux.cfg ]------------------------------------------------------------" 
cp $KICKSTART_FILE $LOCAL_BOOT_PATH/isolinux/ks.cfg
sed -i 's/append\ initrd\=initrd.img/append initrd=initrd.img\ ks\=cdrom:\/ks.cfg/' $LOCAL_BOOT_PATH/isolinux/isolinux.cfg

#copy CORTX packages 
#find -L $CORTX_DEPS_PATH/$OS/$OS_VERSION/ -name '*.rpm' ! -path "$CORTX_DEPS_PATH/$OS/$OS_VERSION/lustre/custom/tcp/*" -exec cp -n {} $LOCAL_BOOT_PATH/Packages/. \;

#Downloading additional packages. Need to optimize
while read -r line
do
echo -e "-------------------------[ Downloading $line package along with dependencies ]--------------------------------" 
yumdownloader --disablerepo=EOS_CentOS-7_CentOS-7-Updates --installroot=/mnt/custom-iso/"$line"-install-root  --destdir=/mnt/custom-iso/custom-packages --resolve "$line"
rm -rf /mnt/custom-iso/"$line"-install-root
cp -n /mnt/custom-iso/custom-packages/* $LOCAL_BOOT_PATH/Packages/.
ls -ltr $LOCAL_BOOT_PATH/Packages/"$line"-*
echo -e "----------------------------------------------[ Done ]---------------------------------------------------------" 
done < additional-packages.txt

#Copy files. 
while read -r line
do
echo "Copying $line package along with dependencies"
find  $CORTX_DEPS_PATH/os -name "$line*" -exec cp "{}" $LOCAL_BOOT_PATH/Packages/ \;
ls -ltr $LOCAL_BOOT_PATH/Packages/"$line"*
done < custom-packages.txt

#Copy Mellanox Packages
cp $CORTX_DEPS_PATH/$OS/$OS_VERSION/performance/linux.mellanox.com/public/repo/mlnx_ofed/4.9-0.1.7.0/rhel7.8/x86_64/MLNX_LIBS/*.rpm $LOCAL_BOOT_PATH/Packages/

pushd $LOCAL_BOOT_PATH
mv repodata/*-c7-minimal-x86_64-comps.xml.gz .
rm -rf repodata/
gunzip ./*-c7-minimal-x86_64-comps.xml.gz 
mv ./*-c7-minimal-x86_64-comps.xml comps.xml
createrepo -g comps.xml .
popd

#generate custom iso file
cd $LOCAL_BOOT_PATH && mkisofs -o $ISO_PATH/$CUSTOM_ISO_VERSION -b isolinux.bin -c boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -V "CentOS 7 x86_64" -R -J -v -T isolinux/. .

#Add md5sum for custom iso
implantisomd5 $ISO_PATH/$CUSTOM_ISO_VERSION

#print ISO location
echo -e "---------------------------------[ Custom ISO locations ]------------------------------------------------------" 
ls -lh /mnt/custom-iso/cortx-custom.iso
md5sum /mnt/custom-iso/cortx-custom.iso
echo -e "-----------------------------------------------[  Done  ]------------------------------------------------------" 
echo "ISO is available at /mnt/custom-iso/cortx-custom.iso"
