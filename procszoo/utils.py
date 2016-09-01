import os
import sys
import pwd
import grp

__all__ = [
    'warn', 'printf', 'i_am_superuser', 'i_am_not_superuser',
    'is_string_or_unicode', 'to_unicode', 'to_bytes', 'find_shell',
    'get_uid_from_name_or_uid', 'get_gid_from_name_or_gid',
    'get_uid_by_name', 'get_gid_by_name', 'get_name_by_uid',
    'get_name_by_gid']


def warn(text=None, newline=True):
    if text is None:
        text = ''
    if newline:
        sys.stderr.write('%s\n' % text)
    else:
        sys.stderr.write(text)


def printf(text=None, newline=True):
    if text is None:
        text = ''
    if newline:
        sys.stdout.write('%s\n' % text)
    else:
        sys.stdout.write(text)

def i_am_superuser():
    return (os.geteuid() == 0)


def i_am_not_superuser():
    return not i_am_superuser()


def is_string_or_unicode(obj):
    if sys.version_info >= (3, 0):
        return isinstance(obj, (str, bytes))
    else:
        return isinstance(obj, basestring)

if sys.version_info >= (3, 0):
    def _to_str(bytes_or_str):
        if isinstance(bytes_or_str, bytes):
            value = bytes_or_str.decode('utf-8')
        else:
            value = bytes_or_str
        return value

    def _to_bytes(bytes_or_str):
        if isinstance(bytes_or_str, str):
            value = bytes_or_str.encode('utf-8')
        else:
            value = bytes_or_str
        return value
else:
    def _to_unicode(unicode_or_str):
        if isinstance(unicode_or_str, str):
            value = unicode_or_str.decode('utf-8')
        else:
            value = unicode_or_str
        return value

    def _to_str(unicode_or_str):
        if isinstance(unicode_or_str, unicode):
            value = unicode_or_str.encode('utf-8')
        else:
            value = unicode_or_str
        return value

def to_unicode(unicode_or_bytes_or_str):
    if sys.version_info >= (3, 0):
        return _to_str(unicode_or_bytes_or_str)
    else:
        return _to_unicode(unicode_or_bytes_or_str)

def to_bytes(unicode_or_bytes_or_str):
    if sys.version_info >= (3, 0):
        return _to_bytes(unicode_or_bytes_or_str)
    else:
        return _to_str(unicode_or_bytes_or_str)

def find_shell(name=None, shell=None):
    if shell is not None:
        return shell
    if name is None:
        name = 'bash'
    fpath =pwd.getpwuid(os.geteuid()).pw_shell
    if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
        if os.path.basename(fpath).endswith('sh'):
            return fpath

    if "SHELL" in os.environ:
        return os.environ.get("SHELL")
    for path in ["/bin", "/usr/bin", "/usr/loca/bin"]:
        fpath = "%s/%s" % (path, name)
        if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
            return fpath
    return "sh"


def get_uid_from_name_or_uid(user_or_uid):
    try:
        uid = int(user_or_uid)
    except ValueError:
        uid = pwd.getpwnam(user_or_uid).pw_uid
    return uid


def get_gid_from_name_or_gid(group_or_gid):
    try:
        gid = int(group_or_gid)
    except ValueError:
        gid = grp.getgrnam(group_or_gid).gr_gid
    return gid


def get_uid_by_name(user):
    return pwd.getpwnam(user).pw_uid


def get_gid_by_name(group):
    return grp.getgrnam(group).gr_gid


def get_name_by_uid(uid):
    return pwd.getpwuid(uid).pw_name


def get_name_by_gid(gid):
    return grp.getgrgid(gid).gr_name
