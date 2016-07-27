m4_define(PROCSZOO_VERSION, 0.95.3)
AC_PREREQ(2.65)
AC_INIT(procszoo, 0.95.3, https://github.com/xning/procszoo)

AC_CHECK_PROG(gcc)

AC_CHECK_HEADERS(sys/syscall.h)

AC_SUBST(NR_SETNS_VAL)
AC_MSG_CHECKING(['SYS_setns' value])
AC_COMPUTE_INT([NR_SETNS_VAL], [SYS_setns], [[#include <sys/syscall.h>]],
  AC_MSG_FAILURE([sys/syscall.h: could not determine 'SYS_setns' value]))
AC_MSG_RESULT([$NR_SETNS_VAL])

AC_SUBST(NR_PIVOT_ROOT_VAL)
AC_MSG_CHECKING(['SYS_pivot_root' value])
AC_COMPUTE_INT([NR_PIVOT_ROOT_VAL], [SYS_pivot_root], [[#include <sys/syscall.h>]],
  AC_MSG_FAILURE([sys/syscall.h: could not determine 'SYS_pivot_root' value]))
AC_MSG_RESULT([$NR_PIVOT_ROOT_VAL])

AC_CONFIG_FILES(procszoo/syscall_numbers.py)
AC_OUTPUT
