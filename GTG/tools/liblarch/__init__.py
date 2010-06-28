# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Gettings Things Gnome! - a personal organizer for the GNOME desktop
# Copyright (c) 2008-2010- Lionel Dricot & Bertrand Rousseau
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

import gobject

from GTG.tools.liblarch.tree import MainTree
from GTG.tools.liblarch.filteredtree import FilteredTree
from GTG.tools.liblarch.filters_bank import FiltersBank

class Tree():
    def __init__(self):
        self.__tree = MainTree()
        self.__fbank = FiltersBank(self.__tree)
        self.mainview = ViewTree(self.__tree,self.__fbank,static=True)

    ###### nodes handling ######
    def get_node(self,nid):
        return self.__tree.get_node(nid)

    def add_node(self,node,parent_id=None):
        node.set_tree(self.__tree)
        self.__tree.add_node(node,parent_id=parent_id)

    def del_node(self,nid):
        return self.__tree.remove_node(nid)

    def refresh_node(self,nid):
        self.__tree.modify_node(nid)
        
    #move the node to a new parent (dismissing all other parents)
    #use pid None to move it to the root
    def move_node(self,nid,new_parent_id=None):
        node = self.get_node(nid)
        toreturn = False
        if node:
            node.set_parent(new_parent_id)
            toreturn = True
        else:
            toreturn = False
        return toreturn
        
    #if pid is None, nothing is done
    def add_parent(self,nid,new_parent_id=None):
        #TODO
        print "add_parent not implemented"
        return

    ############ Views ############
    #The main view is the bare tree, without any filters on it.
    def get_main_view(self):
        return self.mainview
        
    def get_viewtree(self,refresh=True):
        vt = ViewTree(self.__tree,self.__fbank,refresh=refresh)
        return vt

    ########### Filters bank ######
    def list_filters(self):
        """ List, by name, all available filters """
        return self.__fbank.list_filters()

    def add_filter(self,filter_name,filter_func,parameters=None):
        """
        Adds a filter to the filter bank 
        @filter_name : name to give to the filter
        @filter_func : the function that will filter the nodes
        @parameters : some default parameters fot that filter
        Return True if the filter was added
        Return False if the filter_name was already in the bank
        """
        return self.__fbank.add_filter(filter_name,filter_func,parameters=parameters)

    def remove_filter(self,filter_name):
        """
        Remove a filter from the bank.
        Only custom filters that were added here can be removed
        Return False if the filter was not removed
        """
        return self.__fbank.remove_filter(filter_name)

################### ViewTree #####################

class ViewTree(gobject.GObject):

    #Those are the three signals you want to catch if displaying
    #a filteredtree. The argument of all signals is the nid of the node
#    __gsignals__ = {'node-added-inview': (gobject.SIGNAL_RUN_FIRST, \
#                                          gobject.TYPE_NONE, (str, )),
#                    'node-deleted-inview': (gobject.SIGNAL_RUN_FIRST, \
#                                            gobject.TYPE_NONE, (str, )),
#                    'node-modified-inview': (gobject.SIGNAL_RUN_FIRST, \
#                                            gobject.TYPE_NONE, (str, )),}
                                            
    def __init__(self,maintree,filters_bank,refresh=True,static=False):
        gobject.GObject.__init__(self)
        self.__maintree = maintree
        self.static = static
        #If we are static, we directly ask the tree. No need of an
        #FilteredTree layer.
        if static:
            self.__ft = maintree
        else:
            self.__ft = FilteredTree(maintree,filters_bank,refresh=refresh)
        

    #only by commodities
    def get_node(self,nid):
        return self.__maintree.get_node(nid)
        
    def __get_static_node(self,nid):
        toreturn = None
        if self.static:
            if not nid or nid == 'root':
                toreturn = self.__maintree.get_root()
            else:
                toreturn = self.__maintree.get_node(nid)
        else:
            print "should not get a static node in a viewtree"
        return toreturn

    def print_tree(self):
        return self.__ft.print_tree()

    #return a list of nid of displayed nodes
    def get_all_nodes(self):
        return self.__ft.get_all_nodes()

    def get_n_nodes(self,withfilters=[],transparent_filters=True):
        """
        returns quantity of displayed nodes in this tree
        if the withfilters is set, returns the quantity of nodes
        that will be displayed if we apply those filters to the current
        tree. It means that the currently applied filters are also taken into
        account.
        If transparent_filters = False, we only take into account 
        the applied filters that doesn't have the transparent parameters.
        """
        if self.static and len(withfilters) > 0:
            #TODO : raises an error
            print "WARNING: filters cannot be applied to a static tree"
            print "the filter parameter will be dismissed"
        if self.static:
            return len(self.__maintree.get_all_nodes())
        else:
            return self.__ft.get_n_nodes(withfilters=withfilters,\
                                    transparent_filters=transparent_filters)

    def get_node_for_path(self, path):
        return self.__ft.get_node_for_path(path)

    def get_paths_for_node(self, nid):
        #TODO
        print "get_paths_for_node not implemented"
        return

    def next_node(self, nid,pid):
        #TODO
        print "next_node not implemented"
        return

    def node_has_child(self, nid):
        toreturn = False
        if self.static:
            node = self.__get_static_node(nid)
            toreturn = node.has_child()
        else:
            toreturn = self.__ft.node_has_child(nid)
        return toreturn

    #if nid is None, return the number of nodes at the root
    def node_n_children(self, nid=None):
        return len(self.node_all_children(nid))
        
    def node_all_children(self, nid=None):
        toreturn = []
        if self.static:
            node = self.__get_static_node(nid)
            if node:
                toreturn = node.get_children() 
        else:
            toreturn = self.__ft.node_all_children(nid)
        return toreturn

    def node_nth_child(self, nid, n):
        #TODO
        print "node_nth_child not implemented"
        return

    def node_parents(self, nid):
        toreturn = []
        if self.static:
            node = self.__get_static_node(nid)
            if node:
                toreturn = node.get_parents()
        else:
            toreturn = self.__ft.node_parents(nid)
        return toreturn

    def is_displayed(self,nid):
        return self.__ft.is_displayed(nid)

    ####### Change filters #################
    def apply_filter(self,filter_name,parameters=None,\
                     reset=False,refresh=True):
        """
        Applies a new filter to the tree.
        @param filter_name: The name of an already registered filter to apply
        @param parameters: Optional parameters to pass to the filter
        @param reset : optional boolean. Should we remove other filters?
        @param refresh : should we refresh after applying this filter ?
        """
        if self.static:
            print "cannot apply filter on the main static view"
        else:
            self.__ft.apply_filter(filter_name,parameters=parameters,\
                                    reset=reset,refresh=refresh)
        return

    def unapply_filter(self,filter_name,refresh=True):
        """
        Removes a filter from the tree.
        @param filter_name: The name of an already added filter to remove
        """
        if self.static:
            print "cannot apply filter on the main static view"
        else:
            self.__ft.unapply_filter(filter_name, refresh=refresh)
        return

    def reset_filters(self,refresh=True):
        """
        Clears all filters currently set on the tree.
        """
        if self.static:
            print "cannot apply filter on the main static view"
        else:
             self.__ft.reset_filters(refresh=refresh)
        return