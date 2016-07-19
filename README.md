Procszoo
========

Procszoo is a small Python module that gives you full
power to manage your processes by Linux namespaces.

## Contents
- [Goals](#goals)
- [Try It](#try-it)
- [Getting Your Feet Wet with the *namespaces* Module](#getting-your-feet-wet-with-the-namespaces-module)
- [Networks](#networks)
- [Docs](#docs)
- [Known Issues](#known-issues)
- [Functions](#functions)

## Goals
--------

Procszoo aims to provide you a simple but complete tool and
you can use it as a **DSL** or an embeded programming language
which let you operate Linux namespaces by Python.

Procszoo gives a smart *init* program. I get it from
[baseimage-docker](https://github.com/phusion/baseimage-docker).
Thanks a lot, you guys.

Procszoo does not require new version Python and Linux
kernel. We support RHEL 6/CentOS 6.

## Try It
---------

Procszoo only requires Python standard libraries, Hence just clone it
and do as follows you will get an interactve shell.

    git clone https://github.com/xning/procszoo.git
    cd procszoo/bin
    ./richard_parker

If your Linux kernel doesn't support "user" namespaces, you need
run the *richard_parker* as *super user*

    cd procszoo/bin
    sudo ./richard_parker

And now, you can check sth that we are in namespaces

* programs get samll pids, e.g., 1, 2, etc., and there is only *lo* device
and it is down

        ps -ef
        ifconfig -a

* open another terminal, we can see that the namespaces entries are different
from our namespaces

        ls -l /proc/self/ns

* if the kernel support and enable "user" namespaces, we are super user now

        id

* if you have trouble to try the above steps, please reference
[Known Issues](#known-issues).

## Getting Your Feet Wet with the *namespaces* Module
-----------------------------------------------------

First, make sure that the *namespaces* module path in the *sys.path*. You
can add the path as follows

    import sys
    sys.path.append(path_to_namespaces)

then if you want to enable each namespaces that your kernel supports

    from namespaces import *
    
    if __name__ == "__main__":
        spawn_namespaces()

If you need run your own program instead of an interactive *shell*, 

    from namespaces import *
    
    if __name__ == "__main__":
        spawn_namespaces(nscmd=path_to_your_program)

## Networks
-----------

Let's add network to the new namespaces.

Because we will mount namespaces entries by the *bind* flag, we need
run *richard_parker* as the super user.

Except the shell that *richard_parker* will open, we need another
interactive shell to make *veth* devices and add them to the new
"net" namespace.

* create a mount point

        mkdir /tmp/ns

* create namespaces

        sudo ./richard_parker --ns_bind_dir=/tmp/ns

* in *richard_parker*, configure the *lo* device

        ifconfig lo 127.0.0.1/24 up

* in a new terminal, remount the */tmp/ns/net* to */var/run/netns/net*
so *ip* command could operate it

        [ -d /var/run/netns ] | sudo mkdir -p  /var/run/netns
        sudo touch /var/run/netns/ns
        sudo mount --bind /tmp/ns/net /var/run/netns/ns

* in the new terminal, create two devices and set one of it to the new
namespace in a new terminal

        sudo ip link add veth0 type veth peer name veth1
        sudo ip link set dev veth1 netns ns

* in the new terminal, configure *veth0* device

        sudo ifconfig veth0 192.168.0.10/24 up

* in *richard_parker*, configure *veth1*

        ifconfig veth1 192.168.0.11/24 up

* let's say "hello" from the new terminal

        ping -c 3 192.168.0.11

* let's say "hello" from *richard_parker*

        ping -c 3 192.168.0.10

## Docs
-------

* [namespaces(7)](http://man7.org/linux/man-pages/man7/namespaces.7.html)

* [unshare(2)](http://man7.org/linux/man-pages/man2/unshare.2.html)

* [setns(2)](http://man7.org/linux/man-pages/man2/setns.2.html)

* [ip(8)](http://man7.org/linux/man-pages/man8/ip.8.html)

* [mount(2)](http://man7.org/linux/man-pages/man2/mount.2.html)

* [Linux namespaces](https://en.wikipedia.org/wiki/Linux_namespaces)

* [Docker and the PID 1 zombie reaping problem](https://blog.phusion.nl/2015/01/20/docker-and-the-pid-1-zombie-reaping-problem/)

* [Resource management:Linux kernel Namespaces and cgroups](http://www.haifux.org/lectures/299/netLec7.pdf)

* [Containers and Namespaces in the Linux Kernel](https://events.linuxfoundation.org/slides/lfcs2010_kolyshkin.pdf)

## Known Issues
---------------

* os.execv complains "permission deny"

    If running *richard_parker* failed on RHEL/CentOS/Fedora, and get following error
    message like this

    >         os.execv(...)
    >     OSError: [Errno 13] Permission denied

    That's not a bug, please see
    the [comment](https://bugzilla.redhat.com/show_bug.cgi?id=1349789#c7).

* "ip netns" failed on RHRL6/CentOS6 and gave error messages as follows

    >     Object "nets" is unknown, try "ip help".

    To resolve this issue, one way is to build and install iproute package by youself

        wget -c https://repos.fedorapeople.org/repos/openstack/EOL/openstack-icehouse/epel-6/iproute-2.6.32-130.el6ost.netns.2.src.rpm
        mock --rebuild iproute-2.6.32-130.el6ost.netns.2.src.rpm

    if you has a x86_64 workstation, and you can directly download and install
    the iproute package from [here](https://repos.fedorapeople.org/repos/openstack/EOL/openstack-icehouse/epel-6/)

## Functions
---------------------

The *procszoo* exported following functions

- unshare
- setns
- sched\_getcpu
- atfork
- is\_namespace\_available
- spawn_namespaces
- fork
- mount
- gethostname
- sethostname
