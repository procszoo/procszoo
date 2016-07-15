procszoo
========

Procszoo is a small Python module that gives you full
power to manage process by Linux namespaces.

Goals
-----

Procszoo aims to provide you a **simple** but **complete**
tool and you can use it as a **DSL** or an embeded
programming language which let you operate Linux namespaces
by Python.

Procszoo gives a smart *init* program. I get it from
[baseimage-docker](https://github.com/phusion/baseimage-docker).

Procszoo does not require new version Python and Linux
kernel. We support RHEL 6/CentOS 6.

How to try it
-------------

Procszoo only requires Python standard libraries, Hence just clone it
and do as follows you will get a interactve shell.

    git clone https://github.com/xning/procszoo.git
    cd procszoo/bin
    ./richard_park

If your Linux kernel doesn't support "user" namespaces, you need
run the **richard_parker** by **root** user

    cd procszoo/bin
    sudo ./richard_parker

And now, you check that we are in namespaces

* programs get samll pids, e.g., 1, 2, etc., and there is only *lo* network
card that is down

        ps -ef
        ifconfig -a
* open another terminal, we can see that the namespaces files are different

        ls -l /proc/self/ns

* if the kernel support and enable "user" namespaces, we are super user now

        id

How to use it in my projects?
-----------------------------

First, make sure that the *namespaces* module path in the **sys.path**. You
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

Networks
--------

Let's add network to our new namespaces.

Because we will mount namespaces entries by the *bind* flag, we need
run richard_parker as the super user.

Except the shell that richard_parker will open, we need another
interactive shell to make *veth* devices and add them to the right
network namespace.

* create a mount point

        mkdir /tmp/ns

* create namespaces

        sudo ./richard_parker --ns_bind_dir=/tmp/ns

* in *richard_parker*, configure the **lo** device

        ifconfig lo 127.0.0.1/24 up

* in a new terminal, remount the */tmp/ns/net* to */var/run/netns/net*
so **ip** command could operate it

        [ -d /var/run/netns ] | sudo mkdir -p  /var/run/netns
        sudo touch /var/run/netns/ns
        sudo mount --bind /tmp/ns/net /var/run/netns/ns

* in the new terminal, create two devices and set one of it to the new
namespace in a new terminal

        sudo ip link add veth0 type veth peer name veth1
        sudo ip link set dev veth1 netns ns

* in the new terminal, configure **veth0** device

        sudo ifconfig veth0 192.168.122.10/24 up

* in *richard_parker*, configure **veth1**

        ifconfig veth1 192.168.122.11/24 up

* let's say "hello" from the new terminal

        ping -c 3 192.168.0.11

* let's say "hello" from *richard_parker*

        ping -c 3 192.168.0.10

Docs
----

* [namespaces(7)](http://man7.org/linux/man-pages/man7/namespaces.7.html)

* [Linux namespaces](https://en.wikipedia.org/wiki/Linux_namespaces)

* [unshare(2)](http://man7.org/linux/man-pages/man2/unshare.2.html)

* [ip(8)](http://man7.org/linux/man-pages/man8/ip.8.html)

* [mount(2)](http://man7.org/linux/man-pages/man2/mount.2.html)

* [Resource management:Linux kernel Namespaces and cgroups](http://www.haifux.org/lectures/299/netLec7.pdf)

* [Containers and Namespaces in the Linux Kernel](https://events.linuxfoundation.org/slides/lfcs2010_kolyshkin.pdf)
