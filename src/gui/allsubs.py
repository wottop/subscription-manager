#
# Copyright (c) 2010 Red Hat, Inc.
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

import datetime
import os
import gtk
import logging
import gettext
_ = gettext.gettext

from logutil import getLogger
log = getLogger(__name__)
import managerlib

from facts import Facts
from dateselect import DateSelector

prefix = os.path.dirname(__file__)
ALL_SUBS_GLADE = os.path.join(prefix, "data/allsubs.glade")


class AllSubscriptionsTab(object):

    def __init__(self, backend, consumer, facts):
        self.backend = backend
        self.consumer = consumer
        self.facts = facts

        self.all_subs_xml = gtk.glade.XML(ALL_SUBS_GLADE)
        self.all_subs_vbox = self.all_subs_xml.get_widget('all_subs_vbox')

        today = datetime.date.today()
        self.date_selector = DateSelector(self.active_on_date_changed, initial_date=today)

        self.all_subs_xml.signal_autoconnect({
            "on_search_button_clicked": self.search_button_clicked,
            "on_date_select_button_clicked": self.date_select_button_clicked,
        })

        self.subs_store = gtk.ListStore(str, str, str, str, str)
        self.subs_treeview = self.all_subs_xml.get_widget('all_subs_treeview')
        self.subs_treeview.set_model(self.subs_store)
        self._add_column(_("Subscription"), 0)
        self._add_column(_("# Bundled Products"), 1)
        self._add_column(_("Total Contracts"), 2)
        self._add_column(_("Total Subscriptions"), 3)
        self._add_column(_("Available Subscriptions"), 4)

        self.no_hw_match_checkbutton = self.all_subs_xml.get_widget(
                'match_hw_checkbutton')
        self.not_installed_checkbutton = self.all_subs_xml.get_widget(
                'not_installed_checkbutton')
        self.contains_text_checkbutton = self.all_subs_xml.get_widget(
                'contains_text_checkbutton')
        self.contains_text_entry = self.all_subs_xml.get_widget(
                'contain_text_entry')

        self.active_on_checkbutton = self.all_subs_xml.get_widget('active_on_checkbutton')
        self.active_on_entry = self.all_subs_xml.get_widget('active_on_entry')

        # Set the date filter to todays date by default:
        self.active_on_entry.set_text(today.strftime("%Y-%m-%d"))

    def include_incompatible(self):
        """ Return True if we're to include pools which failed a rule check. """
        return self.no_hw_match_checkbutton.get_active()

    def include_uninstalled(self):
        """ 
        Return True if we're to include pools for products that are 
        not installed.
        """
        return self.not_installed_checkbutton.get_active()

    def get_filter_text(self):
        """
        Returns the text to filter subscriptions based on. Will return None
        if the text box is empty, or the filter checkbox is not enabled.
        """
        if self.contains_text_checkbutton.get_active():
            contains_text = self.contains_text_entry.get_text()
            if contains_text != "":
                return contains_text
        return None

    def get_active_on_date(self):
        """
        Returns a datetime for the "active on" filter, if one is selected.
        Otherwise returns None.
        """
        if self.active_on_checkbutton.get_active():
            text = self.active_on_entry.get_text()
            if text != '':
                year, month, day = text.split('-')
                active_on_date = datetime.date(int(year), int(month),
                        int(day))
                return active_on_date
        return None
        
    def load_all_subs(self):
        log.debug("Loading subscriptions.")
        self.subs_store.clear()

        pools = managerlib.list_pools(self.backend.uep,
                self.consumer.uuid, self.facts, all=self.include_incompatible())

        pool_filter = managerlib.PoolFilter()

        # Filter out products that are not installed if necessary:
        if not self.include_uninstalled():
            pools = pool_filter.filter_uninstalled(pools)

        # Filter by product name if necessary:
        if self.get_filter_text():
            pools = pool_filter.filter_product_name(pools, self.get_filter_text())

        if self.get_active_on_date():
            pools = pool_filter.filter_active_on(pools, self.get_active_on_date())

        merged_pools = managerlib.merge_pools(pools)
        for entry in merged_pools.values():
            self.subs_store.append([
                entry.product_name, 
                entry.bundled_products,
                len(entry.pools),
                entry.quantity,
                entry.quantity - entry.consumed,
        ])

    def _add_column(self, name, order):
        column = gtk.TreeViewColumn(name, gtk.CellRendererText(), text=order)
        self.subs_treeview.append_column(column)

    def get_content(self):
        return self.all_subs_vbox

    def get_label(self):
        return _("All Available Subscriptions")

    def search_button_clicked(self, widget):
        """ Reload the subscriptions when the Search button is clicked. """
        log.debug("Search button clicked.")
        log.debug("   include hw mismatch = %s" % self.include_incompatible())
        log.debug("   include uninstalled = %s" % self.include_uninstalled())
        log.debug("   contains text = %s" % self.get_filter_text())
        self.load_all_subs()

    def date_select_button_clicked(self, widget):
        self.date_selector.show()

    def active_on_date_changed(self, widget):
        """
        Callback for the date selector whenever the user has selected a new
        active on date.
        """
        year, month, day = widget.get_date()
        month += 1 # this starts at 0
        self.active_on_entry.set_text("%s-%s-%s" % (year, month, day))