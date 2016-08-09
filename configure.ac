m4_define(PROCSZOO_VERSION, 0.97.1)
AC_INIT(procszoo, PROCSZOO_VERSION, https://github.com/xning/procszoo)

m4_ifdef([AC_COMPUTE_INT], [], [
  AC_DEFUN([AC_COMPUTE_INT], [_AC_COMPUTE_INT([$2],[$1],[$3],[$4])])
])

AC_CHECK_PROG(gcc)

AC_CHECK_HEADERS(syscall.h)

AC_SUBST(NR_PIVOT_ROOT_VAL)
AC_MSG_CHECKING(['__NR_pivot_root' value])
AC_COMPUTE_INT([NR_PIVOT_ROOT_VAL], [__NR_pivot_root], [[#include <syscall.h>]],
  AC_MSG_WARN([syscall.h: could not determine '__NR_pivot_root' value]))
if test "${NR_PIVOT_ROOT_VAL:-}"x != x; then
AC_MSG_RESULT([$NR_PIVOT_ROOT_VAL])
AC_CONFIG_FILES(procszoo/syscall_pivot_root_number.py)
fi

AC_SUBST(NR_SETNS_VAL)
AC_MSG_CHECKING(['__NR_setns' value])
AC_COMPUTE_INT([NR_SETNS_VAL], [__NR_setns], [[#include <syscall.h>]],
  AC_MSG_WARN([syscall.h: could not determine '__NR_setns' value]))
if test "${NR_SETNS_VAL:-}"x != x; then
AC_MSG_RESULT([$NR_SETNS_VAL])
AC_CONFIG_FILES(procszoo/syscall_setns_number.py)
fi

AC_OUTPUT
