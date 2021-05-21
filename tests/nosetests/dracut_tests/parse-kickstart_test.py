#
# Copyright 2015 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.  Any Red Hat
# trademarks that are incorporated in the source code or documentation are not
# subject to the GNU General Public License and may only be used or replicated
# with the express permission of Red Hat, Inc.

import os
import unittest
import tempfile
import shutil
import subprocess

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # create the directory used for file/folder tests
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        # remove the testing directory
        try:
            with open(self.tmpdir + "/ks.info") as f:
                for line in f:
                    if line.startswith("parsed_kickstart="):
                        filename = line.partition("=")[2].strip().replace('"', "")
                        os.remove(filename)
                        break
        except OSError:
            pass

        shutil.rmtree(self.tmpdir)

class ParseKickstartTestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = os.path.abspath(os.path.join(os.environ["top_srcdir"], "dracut/parse-kickstart"))

    def execParseKickstart(self, ks_file):
        try:
            output = subprocess.check_output([self.command, "--tmpdir", self.tmpdir, ks_file], universal_newlines=True)
        except subprocess.CalledProcessError as e:
            return str(e).splitlines()
        return str(output).splitlines()

    def cdrom_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""cdrom """)
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(lines[0], "inst.repo=cdrom", lines)

    def harddrive_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""harddrive --partition=sda4 --dir=/path/to/tree""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(lines[0], "inst.repo=hd:sda4:/path/to/tree", lines)

    def nfs_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""nfs --server=host.at.foo.com --dir=/path/to/tree --opts=nolock,timeo=50""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(lines[0], "inst.repo=nfs:nolock,timeo=50:host.at.foo.com:/path/to/tree", lines)

    def nfs_test_2(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""nfs --server=host.at.foo.com --dir=/path/to/tree""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(lines[0], "inst.repo=nfs:host.at.foo.com:/path/to/tree", lines)

    def url_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""url --url=https://host.at.foo.com/path/to/tree --noverifyssl --proxy=http://localhost:8123""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(len(lines), 3, lines)
        self.assertEqual(lines[0], "inst.repo=https://host.at.foo.com/path/to/tree", lines)
        self.assertEqual(lines[1], "rd.noverifyssl", lines)
        self.assertEqual(lines[2], "inst.proxy=http://localhost:8123", lines)

    def updates_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""updates http://host.at.foo.com/path/to/updates.img""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(lines[0], "live.updates=http://host.at.foo.com/path/to/updates.img", lines)

    def mediacheck_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""mediacheck""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(lines[0], "rd.live.check", lines)

    def driverdisk_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""driverdisk sda5""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(lines[0], "inst.dd=hd:sda5")

    def driverdisk_test_2(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""driverdisk --source=http://host.att.foo.com/path/to/dd""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

        self.assertEqual(lines[0], "inst.dd=http://host.att.foo.com/path/to/dd", lines)

    def network_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""network --device=ens3 --bootproto=dhcp --activate""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            print(lines)
            self.assertEqual(lines[0], "ip=ens3:dhcp: bootdev=ens3")

    def network_test_2(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""network --device=AA:BB:CC:DD:EE:FF --bootproto=dhcp --activate""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "ifname=ksdev0:aa:bb:cc:dd:ee:ff ip=ksdev0:dhcp: bootdev=ksdev0", lines)

    def network_static_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""network --device=ens3 --bootproto=static --ip=10.0.2.15 --netmask=255.255.255.0 --gateway=10.0.2.254 --nameserver=10.0.2.10""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "ip=10.0.2.15::10.0.2.254:255.255.255.0::ens3:none: nameserver=10.0.2.10 bootdev=ens3")

    def network_bond_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""network --device=bond0 --mtu=1500 --bondslaves=enp4s0,enp7s0 --bondopts=mode=active-backup,primary=enp4s0 --bootproto=dhcp""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "ip=bond0:dhcp:1500 bootdev=bond0 bond=bond0:enp4s0,enp7s0:mode=active-backup,primary=enp4s0:1500")

    def network_bond_test2(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            # no --mtu, no --bondopts
            ks_file.write("""network --device=bond0 --bondslaves=enp4s0,enp7s0 --bootproto=dhcp""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "ip=bond0:dhcp: bootdev=bond0 bond=bond0:enp4s0,enp7s0::")

    def network_bond_test3(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            # no --bondopts
            ks_file.write("""network --device=bond0 --bondslaves=enp4s0,enp7s0 --mtu=1500 --bootproto=dhcp""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "ip=bond0:dhcp:1500 bootdev=bond0 bond=bond0:enp4s0,enp7s0::1500")

    def network_bridge_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""network --device br0 --activate --bootproto dhcp --bridgeslaves=eth0 --bridgeopts=stp=6.0,forward_delay=2""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "ip=br0:dhcp: bootdev=br0 bridge=br0:eth0")

    def network_ipv6_only_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""network --noipv4 --hostname=blah.test.com --ipv6=1:2:3:4:5:6:7:8 --ipv6gateway=2001:beaf:cafe::1 --device lo --nameserver=1:1:1:1::,2:2:2:2::""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertRegex(lines[0], r"ip=\[1:2:3:4:5:6:7:8\]:.*")

    def displaymode_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""cmdline""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "inst.cmdline", lines)

    def displaymode_test_2(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""graphical""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "inst.graphical", lines)

    def displaymode_test_3(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""text""")
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "inst.text", lines)

    def bootloader_test(self):
        with tempfile.NamedTemporaryFile(mode="w+t") as ks_file:
            ks_file.write("""bootloader --extlinux """)
            ks_file.flush()
            lines = self.execParseKickstart(ks_file.name)

            self.assertEqual(lines[0], "inst.extlinux", lines)
