'''
This module gives us a lot functions to maintain and to operate interfaces.

To understand following abbreviated worlds please reference rtnetlink(7)
'''
import os
import sys

from procszoo.c_functions import mount
from procszoo.utils import printf
from procszoo.network.exceptions import *
from procszoo.network.dhcp import dhcp_if

__all__ = [
    'Pyroute2ModuleUnvailable', 'Pyroute2NetNSUnvailable',
    'get_all_ifnames', 'get_all_ifindexes', 'get_all_ifnames_and_ifindexes',
    'is_ifindex_wireless', 'is_ifname_wireless',
    'is_all_ifindexes_wireless', 'is_all_ifnames_wireless',
    'get_all_oifindexes_of_default_route', 'get_all_oifnames_of_default_route',
    'create_macvtap', 'add_ifindex_to_ns', 'dhcp_if',
    'add_ifname_to_ns', 'add_ifname_to_ns_by_pid',
    'del_if_by_name', 'del_if_by_index',
    'down_if_by_name', 'up_if_by_name',
    'down_if_by_index', 'up_if_by_index',
    ]


try:
    import pyroute2
except ImportError:
    raise Pyroute2ModuleUnvailable


try:
    pyroute2.NetNS
except AttributeError:
    raise Pyroute2NetNSUnvailable

from pyroute2 import IPRoute
from pyroute2 import NetNS
from pyroute2 import IW
try:
    from pyroute2.netlink.exceptions import NetlinkError
except ImportError:
    from pyroute2.netlink import NetlinkError

PYROUTE2_IW_PACKAGE_AVAILABLE = True
try:
    IW()
except NetlinkError:
    PYROUTE2_IW_PACKAGE_AVAILABLE = False


def get_all_ifnames():
    '''get all interface names'''
    ipr = IPRoute()
    ret = [l.get_attr('IFLA_IFNAME') for l in ipr.get_links()]
    ipr.close()
    return ret

def get_all_ifindexes():
    '''get all interface indexes'''
    ipr = IPRoute()
    ret = [l.get('index') for l in ipr.get_links()]
    ipr.close()
    return ret


def get_all_ifnames_and_ifindexes():
    '''get all interface names and their indexes'''
    ipr = IPRoute()
    ret = [(l.get_attr('IFLA_IFNAME'), l.get('index'))
               for l in ipr.get_links()]
    ipr.close()
    return dict(ret)


if PYROUTE2_IW_PACKAGE_AVAILABLE:
    def is_ifindex_wireless(ifindex):
        '''check whether a interface is wireless or not by the its index'''
        retval = True
        iw = IW()
        try:
            iw.get_interface_by_ifindex(ifindex)
        except NetlinkError:
            retval = False
        finally:
            iw.close()
        return retval


    def is_ifname_wireless(ifname):
        '''check whether a interface is wireless or not by its name'''
        retval = True
        ipr = IPRoute()
        iw = IW()
        index = ipr.link_lookup(ifname=ifname)[0]
        try:
            iw.get_interface_by_ifindex(index)
        except NetlinkError:
            retval = False
        finally:
            iw.close()
            ipr.close()
        return retval


    def is_all_ifindexes_wireless(ifindexes):
        iw = IW()
        ret = {}

        for idx in ifindexes:
            try:
                iw.get_interface_by_ifindex(idx)
            except NetlinkError:
                ret[idx] = False
            else:
                ret[idx] = True

        iw.close()
        return ret


    def is_all_ifnames_wireless(ifnames):
        ipr = IPRoute()
        iw = IW()

        ret = {}
        links = {}

        for l in ipr.get_links():
            links[l.get_attr('IFLA_IFNAME')] = l.get('index')

        unkown_ifnames = [n for n in ifnames if n not in links.keys()]
        if unkown_ifnames:
            raise RuntimeError

        for n in ifnames:
            idx = links[n]

            try:
                iw.get_interface_by_ifindex(idx)
            except NetlinkError:
                ret[n] = False
            else:
                ret[n] = True

        return ret
else:
    from procszoo.network.wrappers import *


def get_all_oifindexes_of_default_route():
    '''return list of all out interface names'''
    ipr = IPRoute()
    idx_list = [r.get_attr('RTA_OIF') for r in ipr.get_default_routes()]
    ipr.close()
    return idx_list


def get_all_oifnames_of_default_route():
    '''return list of all out interface index'''
    ipr = IPRoute()
    idx_list = [r.get_attr('RTA_OIF') for r in ipr.get_default_routes()]
    links = ipr.get_links(idx_list)
    name_list = [l.get_attr('IFLA_IFNAME') for l in links]
    ipr.close()
    return name_list


def create_macvtap(ifname=None, link=None, mode=None, **kwargs):
    if 'kind' in kwargs:
        if kwargs.get('kind') != 'macvtap':
            raise NetworkSettingError
    else:
        kwargs['kind'] = 'mactap'

    if ifname is None:
        ifname = 'nth%d' % os.getpid()
    if mode is None:
        mode = 'vepa'

    ipr = IPRoute()
    if link is None:
        ifs = [idx for idx in get_all_oifindexes_of_default_route()
                   if not is_ifindex_wireless(idx)]
        if not ifs:
            raise RuntimeError('do not know use whick network device')
        else:
            index = ifs[0]
    else:
        try:
            index=int(link)
        except ValueError:
            index = ipr.link_lookup(ifname=link)[0]
        finally:
            ipr.close()

    try:
        ipr.link('add', ifname=ifname, kind='macvtap',
                     link=index, macvtap_mode=mode)
    except:
        raise RuntimeError('failed to create a macvtap device')
    finally:
        ipr.close()


def add_ifindex_to_ns(ifindex, ns):
    ipr = IPRoute()
    try:
        ipr.link('set', index=ifindex, net_ns_fd=ns)
    except Exception:
        printf(e)
        raise RuntimeError
    finally:
        ipr.close()

def add_ifname_to_ns(ifname, ns):
    '''add a interface to the ns net namespace'''
    ipr = IPRoute()
    ifindex = ipr.link_lookup(ifname=ifname)[0]
    try:
        ipr.link('set', index=ifindex, net_ns_fd=ns)
    except Exception:
        printf(e)
        raise RuntimeError
    finally:
        ipr.close()

def add_ifname_to_ns_by_pid(ifname, pid, path=None):
    pid = int(pid)
    netns_dir = '/var/run/netns'
    netns = 'net%d' % pid
    target = '%s/%s' % (netns_dir, netns)

    if not os.path.exists(netns_dir):
        os.makedirs(netns_dir)
    if not os.path.isdir(netns_dir):
        raise RuntimeError('%s is not a dir' % netns_dir)
    if not os.path.exists(target):
        open(target, 'w+').close()

    if path is None:
        path = '/proc/%d/ns/net' % pid
    mount(source=path, target=target, mount_type="bind")
    add_ifname_to_ns(ifname, netns)


def del_if_by_name(ifname):
    ipr = IPRoute()
    ipr.link('remove', ifname=ifname)
    ipr.close()


def del_if_by_index(ifindex):
    ifindex = int(ifindex)
    ipr = IPRoute()
    ipr.link_remove(ifindex)
    ipr.close()

def down_if_by_name(ifname):
    ipr = IPRoute()
    ifindex = ipr.link_lookup(ifname=ifname)[0]
    ipr.link_down(ifindex)
    ipr.close()


def up_if_by_name(ifname):
    ipr = IPRoute()
    ifindex = ipr.link_lookup(ifname=ifname)[0]
    ipr.link_up(ifindex)
    ipr.close()

def down_if_by_index(ifindex):
    ipr = IPRoute()
    ipr.link_down(ifindex)
    ipr.close()


def up_if_by_index(ifindex):
    ipr = IPRoute()
    ipr.link_up(ifindex)
    ipr.close()

def remove_netns(ns_name):
    netns = NetNS(ns_name)
    netns.remove()
    netns.close()

