# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Violin Memory, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Violin Memory tests for iSCSI driver

by Ryan Lucio
Senior Software Engineer
Violin Memory

Note: python documentation for unit testing can be found at
http://docs.python.org/2/library/unittest.html

To run these tests, do the following:

1) Checkout a copy of Cinder folsom and setup the development
environment.  Directions can be found on Openstack's developer site at
http://docs.openstack.org/developer/cinder/devref/development.environment.html

2) If you haven't already, activate the python virtual environment
'source .venv/bin/activate'.

3) Install the cinder code to the virtual env 'python setup.py install'

4) Checkout a copy of the xg-tools and install it into the virtual
environment.  Installation instructions are in the top level INSTALL
file.

5) Run the unit tests with 'python unittest_violin.py'
"""


import unittest
import time
import violin


class testViolin(unittest.TestCase):
    """
    A test class for the violin driver module.
    """
    def stubOpen(self, ip, user, password):
        """ hack to vxg.open() create session without logging in """
        sess = violin.vxg.core.session.XGSession(ip, user, password, False, "https", False)
        return violin.vxg.vshare.VShare(sess)

    def stubLogin(self):
        """ hack to vxg.core.session.XGSession.login() to skip login of
        fake connection """
        return True

    def stubClose(self):
        """ hack to vxg.core.session.XGSession.close() to skip closing
        the fake connection """
        return True

    def stubGetNodeValues(self, node):
        """ hack to vxg.core.session.XGSession.get_node_values() to hard code query
        results """
        idx = self.request_index
        if self.request_index < len(self.dict)-1:
            self.request_index+=1
        return self.dict[idx]

    def stubPerformActionSuccess(self, *args, **kwargs):
        """ hack any function that uses
        violin.vxg.core.session.XGSession.perform_action to just
        return Success """
        return {'code': 0, 'message': 'success'}

    def stubPerformActionFail(self, *args, **kwargs):
        """ hack to any function that uses
        violin.vxg.core.session.XGSession.perform_action to just
        return Failure"""
        return {'code': 1, 'message': 'fail'}

    def stubGenericTrue(self):
        """ generic stub to have any function just return True """
        return True

    def stubGenericFalse(self):
        """ generic stub to have any function just return False """
        return False

    def setUp(self):
        """ Setup the driver flags and use the vxg connections in
        do_setup, but short-circuit the login and force the version
        string.  I am using version G5.5.3 for testing.  Alternate
        versions include G5.0.2, G5.1.0, G5.2.0, G5.5.3, G6.0.0 """
        emptyContext = []
        self.request_index = 0
        self.dict = [{ "/system/version/release": 'G5.5.3' }]
        violin.FLAGS.gateway_vip = "1.1.1.1"
        violin.FLAGS.gateway_mga = "1.1.1.2"
        violin.FLAGS.gateway_mgb = "1.1.1.3"
        violin.vxg.core.session.XGSession.login = self.stubLogin
        violin.vxg.core.session.XGSession.close = self.stubClose
        violin.vxg.core.session.XGSession.get_node_values = self.stubGetNodeValues
        self.driver = violin.ViolinDriver(emptyContext)
        self.driver.do_setup(self)

    def tearDown(self):
        self.driver = None

    # *** check_for_setup() tests ***
    #
    def testCheckForSetupError_NoContainer(self):
        ''' container name is empty '''
        self.driver.container = ""
        self.assertRaises(violin.InvalidBackendConfig, self.driver.check_for_setup_error)
    def testCheckForSetupError_NoDeviceId(self):
        ''' device id is empty '''
        self.driver.device_id = ""
        self.assertRaises(violin.InvalidBackendConfig, self.driver.check_for_setup_error)
    def testCheckForSetupError_NoIscsiConfig(self):
        ''' iscsi is disabled '''
        self.request_index = 0
        self.dict = [{ "/vshare/config/iscsi/enable": False }]
        self.assertRaises(violin.InvalidBackendConfig, self.driver.check_for_setup_error)
    def testCheckForSetupError_NoIgroupConfig(self):
        ''' igroup config binding is empty '''
        self.request_index = 0
        self.dict = [{ "/vshare/config/iscsi/enable": True }]
        self.dict.append({})
        self.assertRaises(violin.InvalidBackendConfig, self.driver.check_for_setup_error)
    def testCheckForSetupError_NoIscsiIPsMga(self):
        ''' iscsi interface binding for mg-a is empty '''
        self.request_index = 0
        self.dict = [{ "/vshare/config/iscsi/enable": True }]
        self.dict.append({ "/vshare/config/igroup/openstack": "openstack" })
        self.dict.append({})
        self.assertRaises(violin.InvalidBackendConfig, self.driver.check_for_setup_error)
    def testCheckForSetupError_NoIscsiIPsMgb(self):
        ''' iscsi interface binding for mg-b is empty '''
        self.request_index = 0
        self.dict = [{ "/vshare/config/iscsi/enable": True }]
        self.dict.append({ "/vshare/config/igroup/openstack": "openstack" })
        self.dict.append({ "/net/interface/config/eth4": "eth4" })
        self.dict.append({ "/net/interface/state/eth4/addr/ipv4/1/ip": "1.1.1.1",
                           "/net/interface/state/eth4/flags/link_up": True})
        self.dict.append({})
        self.assertRaises(violin.InvalidBackendConfig, self.driver.check_for_setup_error)

    # *** _create_lun() tests ***
    #
    def testCreateLun(self):
        volume = {'name': 'vol-01', 'size': '1'}
        violin.ViolinDriver._wait_for_lockstate = self.stubGenericTrue
        self.driver.vmem_vip.lun.create_lun = self.stubPerformActionSuccess
        self.assertIsNone(self.driver._create_lun(volume))
    def testDeleteLun_CreateFails(self):
        volume = {'name': 'vol-01', 'size': '1'}
        violin.ViolinDriver._wait_for_lockstate = self.stubGenericTrue
        self.driver.vmem_vip.lun.create_lun = self.stubPerformActionFail
        self.assertRaises(violin.exception.Error, self.driver._create_lun, volume)

    # *** _delete_lun() tests ***
    #
    def testDeleteLun(self):
        volume = {'name': 'vol-01', 'size': '1'}
        violin.ViolinDriver._wait_for_lockstate = self.stubGenericTrue
        self.driver.vmem_vip.lun.bulk_delete_luns = self.stubPerformActionSuccess
        self.assertIsNone(self.driver._delete_lun(volume))
    def testDeleteLun_DeleteFails(self):
        volume = {'name': 'vol-01', 'size': '1'}
        violin.ViolinDriver._wait_for_lockstate = self.stubGenericTrue
        self.driver.vmem_vip.lun.bulk_delete_luns = self.stubPerformActionFail
        self.assertRaises(violin.exception.Error, self.driver._delete_lun, volume)

    # *** _create_iscsi_target() tests ***
    #

    # *** _delete_iscsi_target() tests ***
    #
    def testDeleteIscsiTarget(self):
        volume = {'name': 'vol-01', 'size': '1'}
        self.driver.vmem_mga.iscsi.unbind_ip_from_target = self.stubPerformActionSuccess
        self.driver.vmem_mgb.iscsi.unbind_ip_from_target = self.stubPerformActionSuccess
        self.driver.vmem_vip.iscsi.delete_iscsi_target = self.stubPerformActionSuccess
        self.assertIsNone(self.driver._delete_iscsi_target(volume))
    def testDeleteIscsiTarget_UnbindFails(self):
        volume = {'name': 'vol-01', 'size': '1'}
        self.driver.vmem_mga.iscsi.unbind_ip_from_target = self.stubPerformActionFail
        self.driver.vmem_mgb.iscsi.unbind_ip_from_target = self.stubPerformActionFail
        self.driver.vmem_vip.iscsi.delete_iscsi_target = self.stubPerformActionSuccess
        self.assertRaises(violin.exception.Error, self.driver._delete_iscsi_target, volume)
    def testDeleteIscsiTarget_DeleteFails(self):
        volume = {'name': 'vol-01', 'size': '1'}
        self.driver.vmem_mga.iscsi.unbind_ip_from_target = self.stubPerformActionSuccess
        self.driver.vmem_mgb.iscsi.unbind_ip_from_target = self.stubPerformActionSuccess
        self.driver.vmem_vip.iscsi.delete_iscsi_target = self.stubPerformActionFail
        self.assertRaises(violin.exception.Error, self.driver._delete_iscsi_target, volume)

    # *** _export_lun() tests ***
    #

    # *** _unexport_lun() tests ***
    #

    # *** _add_igroup_member() tests ***
    #

    # *** _remove_igroup_member() tests ***
    #

    # *** _update_stats() tests ***
    #
    def testUpdateStats(self):
        self.driver.container = "mycontainer"
        self.request_index = 0
        tot_bytes = 100 * 1024 * 1024 * 1024
        alloc_bytes = 0
        backend_string = "V6000"
        vendor_string = "Violin Memory, Inc."
        self.dict = [{ "/vshare/state/global/1/container/mycontainer/total_bytes": tot_bytes,
                       "/vshare/state/global/1/container/mycontainer/alloc_bytes": alloc_bytes,
                       "/media/state/array/mycontainer/chassis/system/type": backend_string,
                       "/hwinfo/state/system_mfr": vendor_string }]
        self.driver._update_stats()
        self.assertEqual(self.driver.stats['total_capacity_gb'], 100)
        self.assertEqual(self.driver.stats['free_capacity_gb'], 100)
        self.assertEqual(self.driver.stats['volume_backend_name'], backend_string)
        self.assertEqual(self.driver.stats['vendor_name'], vendor_string)
    def testUpdateStats_DataQueryFails(self):
        self.driver.container = "mycontainer"
        self.request_index = 0
        self.dict = [{}]
        self.driver._update_stats()
        self.assertEqual(self.driver.stats['total_capacity_gb'], "unknown")
        self.assertEqual(self.driver.stats['free_capacity_gb'], "unknown")
        self.assertEqual(self.driver.stats['volume_backend_name'], "unknown")
        self.assertEqual(self.driver.stats['vendor_name'], "Violin")

    # *** _login() tests ***
    #
    def testLogin_Force(self):
        self.assertTrue(self.driver._login(True))
    def testLogin_NoForce(self):
        self.driver.session_start_time = 0
        self.assertTrue(self.driver._login(False))
    def testLogin_NoUpdate(self):
        self.driver.session_start_time = time.time()
        self.assertFalse(self.driver._login(False))

    # *** _get_lun_id() tests ***
    #
    def testGetLunID_ValidLun(self):
        container = "mycontainer"
        volume = "vol-01"
        iqn = "iqn.2004-02.com.vmem:mydnsname-vol-01"
        igroup = "myigroup"
        node = "/vshare/config/export/container/%s/lun/%s/target/%s/initiator/%s/lun_id" \
            % (container, volume, iqn, igroup)
        self.request_index = 0
        self.dict = [{ node: "1" }]
        self.assertEqual(self.driver._get_lun_id(container, volume, iqn, igroup), "1")
    def testGetLunID_InvalidLun(self):
        container = "mycontainer"
        volume = "vol-01"
        iqn = "iqn.2004-02.com.vmem:mydnsname-vol-01"
        igroup = "myigroup"
        node = "/vshare/config/export/container/%s/lun/%s/target/%s/initiator/%s/lun_id" \
            % (container, volume, iqn, igroup)
        self.assertRaises(KeyError, self.driver._get_lun_id, container, volume, iqn, igroup)

    # *** _get_short_name() tests ***
    #
    def testGetShortName_LongName(self):
        long_name = "abcdefghijklmnopqrstuvwxyz1234567890"
        short_name = "abcdefghijklmnopqrstuvwxyz123456"
        self.assertEqual(self.driver._get_short_name(long_name), short_name)
    def testGetShortName_ShortName(self):
        long_name = "abcdef"
        short_name = "abcdef"
        self.assertEqual(self.driver._get_short_name(long_name), short_name)
    def testGetShortName_EmptyName(self):
        long_name = ""
        short_name = ""
        self.assertEqual(self.driver._get_short_name(long_name), short_name)

    # *** _iscsi_location() tests ***
    #
    def testIscsiLocation(self):
        ip = "1.1.1.1"
        port = "1234"
        iqn = "iqn.2004-02.com.vmem:mydnsname-vol-01"
        lun = "vol-01"
        expected = "1.1.1.1:1234, iqn.2004-02.com.vmem:mydnsname-vol-01 vol-01"
        self.assertEqual(self.driver._iscsi_location(ip, port, iqn, lun), expected)

    # *** _wait_for_exportstate() tests ***
    #
    def testWaitForExportState(self):
        self.request_index = 0
        self.dict = [{ "/vshare/config/export/container/1/lun/vol-01": "vol-01" }]
        self.assertTrue(self.driver._wait_for_exportstate("vol-01", True))
    def testWaitForExportState_NoState(self):
        self.request_index = 0
        self.dict = [{}]
        self.assertFalse(self.driver._wait_for_exportstate("vol-01", False))

    # *** _wait_for_lockstate() tests ***
    #

    # *** _get_active_iscsi_ips() tests ***
    #
    def testGetActiveIscsiIPs(self):
        self.request_index = 0
        self.dict = [{ "/net/interface/config/eth4": "eth4" }]
        self.dict.append({ "/net/interface/state/eth4/addr/ipv4/1/ip": "1.1.1.1",
                           "/net/interface/state/eth4/flags/link_up": True})
        ips = self.driver._get_active_iscsi_ips(self.driver.vmem_vip)
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], "1.1.1.1")
    def testGetActiveIscsiIPs_InvalidIntfs(self):
        self.request_index = 0
        self.dict = [{ "/net/interface/config/lo": "lo",
                       "/net/interface/config/vlan10": "vlan10",
                       "/net/interface/config/eth1": "eth1",
                       "/net/interface/config/eth2": "eth2",
                       "/net/interface/config/eth3": "eth3" }]
        ips = self.driver._get_active_iscsi_ips(self.driver.vmem_vip)
        self.assertEqual(len(ips), 0)
    def testGetActiveIscsiIps_NoIntfs(self):
        self.request_index = 0
        self.dict = [{}]
        ips = self.driver._get_active_iscsi_ips(self.driver.vmem_vip)
        self.assertEqual(len(ips), 0)

    # *** _get_hostname() tests ***
    #
    def testGetHostname(self):
        self.request_index = 0
        self.dict = [{ "/system/hostname": "MYHOST" }]
        self.assertEqual(self.driver._get_hostname(None), "MYHOST")
    def testGetHostname_QueryFails(self):
        self.request_index = 0
        self.dict = [{}]
        self.assertEqual(self.driver._get_hostname(None), violin.FLAGS.gateway_vip)
    def testGetHostname_Mga(self):
        self.request_index = 0
        self.dict = [{ "/system/hostname": "MYHOST" }]
        self.assertEqual(self.driver._get_hostname('mga'), "MYHOST")
    def testGetHostName_MgaQueryFails(self):
        self.request_index = 0
        self.dict = [{}]
        self.assertEqual(self.driver._get_hostname('mga'), violin.FLAGS.gateway_mga)
    def testGetHostname_Mgb(self):
        self.request_index = 0
        self.dict = [{ "/system/hostname": "MYHOST" }]
        self.assertEqual(self.driver._get_hostname('mgb'), "MYHOST")
    def testGetHostName_MgbQueryFails(self):
        self.request_index = 0
        self.dict = [{}]
        self.assertEqual(self.driver._get_hostname('mgb'), violin.FLAGS.gateway_mgb)

def suite():
    suite = unittest.TestSuite()
    suite.addtest(unittest.makeSuite(testViolin))
    return suite

if __name__ == "__main__":
    unittest.main()

