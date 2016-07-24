__all__ = [
    "NamespaceGenericException", "UnknownNamespaceFound",
    "UnavailableNamespaceFound", "NamespaceSettingError"]

class NamespaceGenericException(Exception):
    #status is copy from mock/py/mockbuild/exception.py
    def __init__(self, namespaces=None, status=80):
        Exception.__init__(self)
        if namespaces:
            self.msg = "NamespaceGenericException: " % ", ".join(namespaces)
        else:
            self.msg = "NamespacesGenericException"
        self.resultcode = status

    def __str__(self):
        return self.msg

class UnknownNamespaceFound(NamespaceGenericException):
    def __init__(self, namespaces=None):
        if namespaces:
            self.msg = "unknown namespaces found: %s" % ", ".join(namespaces)
        else:
            self.msg = "unknown namespaces found"

    def __str__(self):
        return self.msg

class UnavailableNamespaceFound(NamespaceGenericException):
    def __init__(self, namespaces=None):
        if namespaces:
            self.msg = "unavailable namespaces found: %s" % ", ".join(namespaces)
        else:
            self.msg = "unavailable namespaces found"

    def __str__(self):
        return self.msg

class NamespaceSettingError(NamespaceGenericException):
    def __init__(self, str=None):
        if str:
            self.msg = "namespaces setting error: %s" % str
        else:
            self.msg = "namespaces setting error"

    def __str__(self):
        return self.msg
