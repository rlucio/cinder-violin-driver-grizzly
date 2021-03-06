cinder-violin-driver-grizzly
============================

Violin Memory v6000 volume driver for Openstack Cinder 'Grizzly'
release.

This repository contains the latest open-source release of Violin
Memory's python driver for use with Openstack Cinder's block storage
services.

It is maintained externally for 3rd party developers, testers, and
users and may be periodically updated in the future.

Setup
-----

1. Download a zip file of this repository (using the "Download ZIP"
button to the right). Unzip the file on the machine(s) running
Cinder's volume service (cinder-volume).

2. Install the 'xg-tools'.  Installation instructions can be found in
the un-tarred vxg directory.

3. Copy the 'violin.py' source file to the drivers section of the
cinder libraries.

    Example: cp violin.py /usr/local/lib/python2.7/dist-packages/cinder/volume/drivers

4. Create an openstack igroup on the Violin v6xxx array.

    'igroup create name openstack'

5. If you haven't setup iSCSI on your array, follow your system
   documentation to enable iSCSI and configure your HBAs with
   appropriate IP addresses.

6. Configure cinder to use the violin driver (see below).

7. Restart cinder-volume.

Configuration
-------------

You will need to alter your cinder configuation, typically in
/etc/cinder/cinder.conf.

The following list shows all of the available options and their
default values:

    # IP address or hostname of the v6000 master VIP (string
    # value)
    gateway_vip=

    # IP address or hostname of mg-a (string value)
    gateway_mga=

    # IP address or hostname of mg-b (string value)
    gateway_mgb=

    # User name for connecting to the Memory Gateway (string
    # value)
    gateway_user=admin

    # User name for connecting to the Memory Gateway (string
    # value)
    gateway_password=

    # IP port to use for iSCSI targets (integer value)
    gateway_iscsi_port=3260

    # prefix for iscsi volumes (string value)
    gateway_iscsi_target_prefix=iqn.2004-02.com.vmem:

    # name of igroup for initiators (string value)
    gateway_iscsi_igroup_name=openstack

A typical configuration file section for using the Violin driver might
look like this:

    volume_driver=cinder.volume.drivers.violin.ViolinDriver
    gateway_vip=1.2.3.4
    gateway_mga=1.2.3.5
    gateway_mgb=1.2.3.6

Note: if you add the configuration option 'verbose=True' and/or
'debug=True' to cinder.conf, you will receive helpful logging from the
Violin driver in /var/log/cinder/cinder-volume.log.

Questions?
----------

For questions or support regarding the driver or its support
libraries, please contact opensource@vmem.com.