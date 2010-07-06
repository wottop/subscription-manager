#
# Copyright (c) 2010 Red Hat, Inc.
#
# Authors: Jeff Ortel <jortel@redhat.com>
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

import sys
sys.path.append('/usr/share/rhsm')
from yum.plugins import TYPE_CORE
from productid import ProductManager

requires_api_version = '2.6'
plugin_type = (TYPE_CORE,)

def postverifytrans_hook(conduit):
    try:
        pm = ProductManager()
        pm.update(conduit._base)
        conduit.error(2, 'Installed products updated.')
    except Exception, e:
        conduit.error(2, str(e))
