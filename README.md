procszoo
========

Procszoo is a small Python module that gives you full
power to manage process by Linux namespaces.

Goals
-----

Procszoo aims to provide a **simple** but **complete**
workbench hence we can operate Linux namespaces by
Python.

Procszoo does not require new version Python and Linux
kernel. We support RHEL 6/CentOS 6.

How to try it
-------------

Procszoo only requires Python stand libraries, Hence just clone it.

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

