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

    ps -ef
    ifconfig -a

How to use it in my projects?
-----------------------------

First, make sure that the **namespaces** module path in the **sys.path**,
then

    from namespaces import *
    
    if __name__ == "__main__":
        spawn_namespaces()

If you need run your program instead of an interactive **shell**, 

    from namespaces import *
    
    if __name__ == "__main__":
        spawn_namespaces(nscmd=path_to_your_program)
        
Docs
----

* [namespaces(7)](http://man7.org/linux/man-pages/man7/namespaces.7.html)

* [Linux namespaces](https://en.wikipedia.org/wiki/Linux_namespaces)

* [unshare(2)](http://man7.org/linux/man-pages/man2/unshare.2.html)

* [Resource management:Linux kernel Namespaces and cgroups](http://www.haifux.org/lectures/299/netLec7.pdf)

* [Containers and Namespaces in the Linux Kernel](https://events.linuxfoundation.org/slides/lfcs2010_kolyshkin.pdf)

