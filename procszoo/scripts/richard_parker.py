import os
import sys
import re
import tempfile
import atexit
from argparse import ArgumentParser, REMAINDER
import traceback
from procszoo.c_functions import *
from procszoo.utils import *
from procszoo.network import *

def get_options():
    propagation_types = get_available_propagations()
    available_namespaces = [
        ns_status[0] for ns_status in show_namespaces_status()
                                 if ns_status[1]]
    prog = os.path.basename(sys.argv[0]) or 'richard_parker'
    project_url = "http://github.com/procszoo/procszoo"
    description = "%s, %s" % (
        'A simple cli to create new namespaces env',
        'default it will enable each available namespaces.')
    parser = ArgumentParser(
        usage="%s [options] [nscmd]" % prog,
        description=description,
        epilog="%s is part of procszoo: %s"  % (prog, project_url))

    parser.add_argument('-v', '--version', action='version',
                            version='%s %s' %  (prog, __version__))
    parser.add_argument("-n", "--namespace", action="append",
                            dest="namespaces", choices=available_namespaces,
                            help="namespace that should be create")
    parser.add_argument("-N", "--negative-namespace", action="append",
                          dest="negative_namespaces",
                          choices=available_namespaces,
                          help="namespace that should not be create")
    parser.add_argument("-i", "--interactive", action="store_true",
                            dest="interactive", default=True,
                            help="enable interactive mode")
    parser.add_argument('-B', '--batch', action="store_false",
                            dest="interactive",
                            help='enable batch mode')
    help_str = "map current effective user/group to root/root, implies -n user"
    parser.add_argument("-r", "--maproot", action="store_true", dest="maproot",
                            default=True, help=help_str)
    parser.add_argument("--no-maproot", action="store_false", dest="maproot")
    parser.add_argument("-u", "--user-map", action="append", dest="users_map",
                            metavar='name_or_uid',
                            type=str,
                            help="user map settings, implies -n user")
    parser.add_argument("-g", "--group-map", action="append",
                            dest="groups_map", type=str, metavar='name_or_gid',
                            help="group map settings, implies -n user")
    parser.add_argument("--init-program", action="store", dest="init_prog",
                            type=str, metavar='your_init_program',
                            help="replace the my_init program by yours")
    parser.add_argument(
        "-s", "--setgroups", action="store", type=str, dest="setgroups",
        choices=['allow', 'deny'],
        help="""control the setgroups syscall in user namespaces,
        when setting to 'allow' will enable --no-maproot option and avoid
        --user-map and --group-map options""")
    parser.add_argument("--mountproc", action="store_true", dest="mountproc",
                        help="remount procfs mountpoin, implies -n mount",
                      default=True)
    parser.add_argument("--no-mountproc", action="store_false",
                            dest="mountproc",
                            help="do not remount procfs")
    parser.add_argument("--mountpoint", action="store", type=str,
                        dest="mountpoint",
                        help="dir that the new procfs would be mounted to")
    parser.add_argument("-b", "--ns-bind-dir", action="store", type=str,
                        dest="ns_bind_dir", metavar='dir',
                        help="dir that the new namespaces would be mounted to")
    parser.add_argument(
        "--propagation", action="store", type=str, dest="propagation",
        choices=propagation_types,
        help="modify mount propagation in mount namespace")
    parser.add_argument("-l", "--list", action="store_true",
                          dest="show_ns_status", default=False,
                          help="list namespaces status")
    parser.add_argument(
        "--hostname", action="store", type=str, dest="hostname",
        metavar='hostname',
        help="hostname in the new net namespaces")
    parser.add_argument(
        "--nameserver", action="append", type=str, dest="nameservers",
        metavar='nameserver', help="nameserver in the new net namespaces")
    parser.add_argument(
        "--network", action="store", nargs='?', type=str, dest="network",
        choices=['macvtap', 'veth'], const='macvtap',
        help="network type")
    parser.add_argument(
        "--bridge", action="store", type=str, dest="bridge", metavar='bridge',
        help='bridge in parent namespaces')
    parser.add_argument("--available-c-functions", action="store_true",
                        dest="show_available_c_functions",
                        help="show available C functions",
                        default=False)
    parser.add_argument('nscmd', nargs=REMAINDER, action="store", default=None)

    return parser.parse_args()


def get_extra(args):
    extra = None
    if args.network:
        extra = {}
        extra['trigger_key'] = 'richard+network'
        extra['data'] = {}
        data = extra['data']
        data['network'] = args.network
        if args.nameservers:
            data['nameservers'] = args.nameservers
        if args.hostname:
            data['hostname'] = args.hostname
        if args.bridge:
            data['bridge'] = args.bridge

    return extra


def set_trigger_for_network(extra):
    if extra:
        workbench.register_spawn_namespaces_trigger(
            'richard+network', _richard_parker_and_network)


def _richard_parker_and_network(**kwargs):
    SpawnNSAndNetwork(**kwargs).entry_point()


def show_namespaces_then_quit():
    for v in show_namespaces_status():
        printf("%-6s: %-5s" % v)
    sys.exit(0)


def show_available_c_functions_and_quit():
    printf("%s" % "\n".join(workbench.show_available_c_functions()))
    sys.exit(0)


def main():
    check_namespaces_available_status()
    args = get_options()
    if args.network is not None and not args.network:
        args.network = 'macvtap'

    if args.show_ns_status:
        show_namespaces_then_quit()
    if args.show_available_c_functions:
        show_available_c_functions_and_quit()

    extra = get_extra(args)
    set_trigger_for_network(extra)

    _exit_code = 0
    try:
        spawn_namespaces(
            namespaces=args.namespaces,
            negative_namespaces=args.negative_namespaces,
            maproot=args.maproot,
            mountproc=args.mountproc,
            mountpoint=args.mountpoint,
            ns_bind_dir=args.ns_bind_dir,
            propagation=args.propagation,
            nscmd=args.nscmd, users_map=args.users_map,
            groups_map=args.groups_map,
            setgroups=args.setgroups,
            init_prog=args.init_prog,
            interactive=args.interactive,
            extra=extra)
    except UnavailableNamespaceFound as e:
        printf(e)
        _exit_code = 1
    except NamespaceRequireSuperuserPrivilege as e:
        printf(e)
        _exit_code = 1
    except NamespaceSettingError as e:
        printf(e)
        _exit_code = 1
    except SystemExit:
        _exit_code = 0
    except Exception as e:
        printf(e)
        traceback.print_exc()
        _exit_code = 1
    sys.exit(_exit_code)


class SpawnNSAndNetwork(SpawnNamespacesConfig):
    def __init__(self, **kwargs):
        super(SpawnNSAndNetwork, self).__init__(**kwargs)
        self._if_prefix = 'nth'
        self.tmpdir = tempfile.gettempdir()
        self.bottom_halves_before_fork = self._bottom_halves_before_fork
        self.top_halves_before_sync = self._top_halves_before_sync
        self.top_halves_half_sync = self._top_halves_half_sync
        self.bottom_halves_after_sync = self._bottom_halves_after_sync

    def _if_name(self, pid=None, ifname=None):
        if ifname is not None:
            return ifname
        if pid is None:
            pid = os.getpid()
        return '%s%d' % (self._if_prefix, pid)

    def need_super_privilege(self):
        return os.geteuid() != 0

    def _bottom_halves_before_fork(self):
        if 'net' in self.namespaces:
            self._netns_created = True
        else:
            self._netns_created = False
        if  get_all_oifindexes_of_default_route():
            self._dhcp_if = True
        else:
            self._dhcp_if = False

        if self._netns_created:
            ifname = self._if_name()
            self._ifname = {'name': ifname, 'type': 'macvtap'}
        self.default_bottom_halves_before_fork()

    def _top_halves_before_sync(self):
        if 'net' in self.namespaces:
            self._netns_created = True
        else:
            self._netns_created = False
        if  get_all_oifindexes_of_default_route():
            self._dhcp_if = True
        else:
            self._dhcp_if = False

        self.default_top_halves_before_sync()

    def _cleaner(self):
        for p in self._leases, self.resolv_conf:
            os.unlink(p)
        del_netns_by_name(self.netns)

    def _top_halves_half_sync(self):
        if self._netns_created:
            ifname = self._if_name(pid=self.top_halves_child_pid)
            create_macvtap(ifname=ifname)
            self._ifname = {'name': ifname, 'type': 'macvtap'}
            self._leases = '/var/run/dhclient-%s.leases' % ifname
        if self._netns_created:
            self.resolv_conf = '%s/.%s' % (self.tmpdir, ifname)
            self.netns = 'net%d' % self.bottom_halves_child_pid
            add_ifname_to_ns_by_pid(self._ifname['name'], self.bottom_halves_child_pid)

        atexit.register(self._cleaner)
        self.default_top_halves_half_sync()

    def _bottom_halves_after_sync(self):
        up_if_by_name('lo')
        ifname = self._ifname['name']
        if self._netns_created:
            up_if_by_name(ifname)
            self._leases = '/var/run/dhclient-%s.leases' % ifname
            self.resolv_conf = '%s/.%s' % (self.tmpdir, ifname)

            if self._dhcp_if:
                dhcp_if(ifname, leases=self._leases)
                nameservers = None
                if os.path.exists(self._leases):
                    regex = re.compile('^ +option domain-name-servers ')
                    hdr = open(self._leases, 'r')
                    for line in hdr:
                        if regex.match(line):
                            pieces = line.split()[2].split(',')
                            nameservers = [l.rstrip(';') for l in pieces]
                            break
                    hdr.close()

                if nameservers:
                    path = self.resolv_conf
                    hdr = open(path, 'w+')
                    hdr.write('# richard_parker created and edited this file\n')
                    for nameserver in nameservers:
                        hdr.write('nameserver %s\n' % nameserver)
                    hdr.close()
                    mount(source=path, target='/etc/resolv.conf', mount_type='bind')

        self.default_bottom_halves_after_sync()


if __name__ == "__main__":
    main()
