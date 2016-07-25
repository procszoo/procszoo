import os

if os.uname()[0] != "Linux":
    raise ImportError("only support Linux platform")

__all__ = [
    "Namespace", "Namespaces",
    "NamespaceGenericException", "UnknownNamespaceFound",
    "UnavailableNamespaceFound", "NamespaceSettingError"]

from namespaces import *
