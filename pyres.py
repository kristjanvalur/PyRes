# todo: implement http://www.skynet.ie/~caolan/publink/winresdump/winresdump/doc/resfmt.txt

import ctypes
import ctypes.wintypes
import sys
import os
import contextlib
import argparse

from ctypes import WINFUNCTYPE, cast
from ctypes.wintypes import (
    HMODULE,
    LPCWSTR,
    HANDLE,
    WORD,
    DWORD,
    LPVOID,
    BOOL,
    HRSRC,
    HGLOBAL,
)


kernel32 = ctypes.windll.kernel32

# ctypes functions

prototype = WINFUNCTYPE(HMODULE, LPCWSTR, HANDLE, DWORD)
LoadLibraryEx = prototype(("LoadLibraryExW", kernel32), ((1,), (1,), (1,)))

prototype = WINFUNCTYPE(BOOL, HMODULE)
FreeLibrary = prototype(("FreeLibrary", kernel32), ((1,),))


EnumResourceNameCallback = ctypes.WINFUNCTYPE(
    BOOL,
    HMODULE,
    LPVOID,
    LPVOID,  # must be void so that it won't try to create strings
    LPVOID,
)

EnumResourceNames = ctypes.windll.kernel32.EnumResourceNamesW
prototype = WINFUNCTYPE(BOOL, HMODULE, LPCWSTR, EnumResourceNameCallback, LPVOID)
EnumResourceNames = prototype(
    ("EnumResourceNamesW", kernel32), ((1,), (1,), (1,), (1,))
)

prototype = WINFUNCTYPE(HRSRC, HMODULE, LPCWSTR, LPCWSTR)
FindResource = prototype(("FindResourceW", kernel32), ((1,), (1,), (1,)))

prototype = WINFUNCTYPE(DWORD, HMODULE, HRSRC)
SizeofResource = prototype(("SizeofResource", kernel32), ((1,), (1,)))

prototype = WINFUNCTYPE(HGLOBAL, HMODULE, HRSRC)
LoadResource = prototype(("LoadResource", kernel32), ((1,), (1,)))

prototype = WINFUNCTYPE(BOOL, HGLOBAL)
FreeResource = prototype(("FreeResource", kernel32), ((1,),))

prototype = WINFUNCTYPE(LPVOID, HGLOBAL)
LockResource = prototype(("LockResource", kernel32), ((1,),))


CloseHandle = ctypes.windll.kernel32.CloseHandle

prototype = WINFUNCTYPE(HANDLE, LPCWSTR, BOOL)
BeginUpdateResource = prototype(("BeginUpdateResourceW", kernel32), ((1,), (1,)))

prototype = WINFUNCTYPE(BOOL, HANDLE, BOOL)
EndUpdateResource = prototype(("EndUpdateResourceW", kernel32), ((1,), (1,)))

prototype = WINFUNCTYPE(BOOL, HANDLE, LPCWSTR, LPCWSTR, WORD, LPVOID, DWORD)
UpdateResource = prototype(
    ("UpdateResourceW", kernel32), ((1,), (1,), (1,), (1,), (1,), (1,))
)


def IS_INTRESOURCE(v: LPVOID):
    return int(v) >> 16 == 0


def MAKEINTRESOURCE(r):
    return cast(r, LPCWSTR)


def RESOURCE_PARM(v: LPVOID):
    # use in the callback
    if IS_INTRESOURCE(v):
        return int(v)
    r = ctypes.wstring_at(v)
    if r.startswith("#"):
        return int(r[1:])
    return r


def RESOURCE_ARG(v):
    if isinstance(v, int):
        return MAKEINTRESOURCE(v)
    return v


# resource types
RT_CURSOR = 1  # Hardware-dependent cursor resource.
RT_BITMAP = 2  # Bitmap resource.
RT_ICON = 3  # Hardware-dependent icon resource.
RT_MENU = 4  # Menu resource.
RT_DIALOG = 5  # Dialog box.
RT_STRING = 6  # String-table entry.
RT_FONTDIR = 7  # Font directory resource.
RT_FONT = 8  # Font resource.
RT_ACCELERATOR = 9  # Accelerator table.
RT_RCDATA = 10  # Application-defined resource (raw data.)
RT_MESSAGETABLE = 11  # Message-table entry.
RT_VERSION = 16  # Version resource.
RT_DLGINCLUDE = 17  # Allows a resource editing tool to associate a string with an .rc file. Typically, the string is the name of the header file that provides symbolic names. The resource compiler parses the string but otherwise ignores the value. For example,
RT_PLUGPLAY = 19  # Plug and Play resource.
RT_VXD = 20  # VXD.
RT_ANICURSOR = 21  # Animated cursor.
RT_ANIICON = 22  # Animated icon.
RT_HTML = 23  # HTML resource.
RT_MANIFEST = 24  # Side-by-Side Assembly Manifest.
RT_GROUP_CURSOR = RT_CURSOR + 11  # Hardware-independent cursor resource.
RT_GROUP_ICON = RT_ICON + 11  # Hardware-independent icon resource.

# LoadLibrary flags
DONT_RESOLVE_DLL_REFERENCES = 0x1
LOAD_LIBRARY_AS_DATAFILE = 0x2
LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x20

# locales
LOCAL_EN_US = 1033


def FormatError(extra=""):
    if extra:
        return f"{extra}: {ctypes.FormatError()}"
    return ctypes.FormatError()


def WinError(extra=""):
    return ctypes.WinError(descr=FormatError(extra))


# useful context managers


@contextlib.contextmanager
def load_library(filename):
    module = LoadLibraryEx(
        filename,
        None,
        DONT_RESOLVE_DLL_REFERENCES
        | LOAD_LIBRARY_AS_DATAFILE
        | LOAD_LIBRARY_AS_IMAGE_RESOURCE,
    )
    if not module:
        raise WinError(filename)
    try:
        yield module
    finally:
        FreeLibrary(module)


@contextlib.contextmanager
def load_resource(hModule, hResource):
    hData = LoadResource(hModule, hResource)
    if not hData:
        print(ctypes.FormatError())
        return False
    try:
        yield hData
    finally:
        FreeResource(hData)


@contextlib.contextmanager
def update_resource(filename):
    update_handle = BeginUpdateResource(filename, False)
    if not update_handle:
        raise WinError("BeginUpdateResource")
    try:
        yield update_handle
    finally:
        ret = EndUpdateResource(update_handle, False)
        if not ret:
            raise WinError("EndUpdateResource")


class ResourceEditor(object):
    def __init__(self, filename, args):
        self.filename = filename
        self.args = args

    def update_resources(self, resources):
        language = LOCAL_EN_US
        with update_resource(self.filename) as update_handle:
            for type, name, data in resources:
                # print(type, name, language, len(data))
                if data is not None:
                    ret = UpdateResource(
                        update_handle,
                        RESOURCE_ARG(type),
                        RESOURCE_ARG(name),
                        language,
                        data,
                        len(data),
                    )
                else:
                    # delete the resource
                    ret = UpdateResource(
                        update_handle,
                        RESOURCE_ARG(type),
                        RESOURCE_ARG(name),
                        language,
                        None,
                        0,
                    )
                if not ret:
                    raise WinError("UpdateResource")

                # print("update: %s" % ret)
        return True

    def get_resources(self, resource_types):
        """Retrieves the manifest(s) embedded in the current executable"""

        manifests = []

        def callback(hModule, lpType, lpName, lParam):
            try:
                lpType = RESOURCE_PARM(lpType)
                lpName = RESOURCE_PARM(lpName)
                # print(f"cb {hModule}, {lpType}, {lpName}, {lParam}")
                hResource = FindResource(
                    hModule, RESOURCE_ARG(lpName), RESOURCE_ARG(lpType)
                )
                if not hResource:
                    print(ctypes.FormatError())
                    return False
                # print self.get_resource_string(hResource)
                size = SizeofResource(hModule, hResource)
                if not size:
                    print(ctypes.FormatError())
                    return False
                with load_resource(hModule, hResource) as hData:
                    ptr = LockResource(hData)
                    if not ptr:
                        print(ctypes.FormatError())
                        return False
                    manifests.append((lpType, lpName, ctypes.string_at(ptr, size)))

                return True
            except Exception as e:
                print(e)
                return False

        with load_library(self.filename) as module:
            for resource_type in resource_types:
                v = EnumResourceNames(
                    module,
                    MAKEINTRESOURCE(resource_type),
                    EnumResourceNameCallback(callback),
                    None,
                )
                if not v:
                    raise WinError("EnumResourceNames")

        repr = [(m[0], m[1], f"{len(m[2])} bytes") for m in manifests]
        if self.args.verbose:
            print(f"manifests: {repr}")
        return manifests


def resource_types(args):
    types = [RT_GROUP_ICON, RT_ICON]
    if args.copy_version:
        types.append(RT_VERSION)
    return types


def clone_file(source, dest, args):
    re_src = ResourceEditor(source, args)
    re_dst = ResourceEditor(dest, args)

    types = resource_types(args)
    src_resources = re_src.get_resources(types)
    dst_resources = re_dst.get_resources(types)
    wrt_resources = src_resources[:]

    # find any extra resources ICON_GROUP resources in the destination
    src_res = {m[:2] for m in src_resources}
    dst_res = {m[:2] for m in dst_resources}
    extra_res = dst_res - src_res
    if extra_res:
        if args.verbose:
            print(f"extra resources in destination: {extra_res}")
        if args.remove_extra:
            for res in extra_res:
                for e in dst_resources:
                    if e[:2] == res:
                        e = list(e)
                        e[2] = None
                        wrt_resources.append(tuple(e))

    if not args.dry_run:
        return re_dst.update_resources(wrt_resources)
    else:
        print("dry run")
        print("would update with:")
        for resource in wrt_resources:
            print(format_resource_tuple(resource))


def format_resource_tuple(resource):
    data = "None" if resource[2] is None else f"{len(resource[2])} bytes"
    return f"{resource[0]}, {resource[1]}, {data}"


def describe_file(source, args):
    re_from = ResourceEditor(source, args)

    resources = re_from.get_resources(resource_types(args))
    repr = [(m[0], m[1], f"{len(m[2])} bytes") for m in resources]
    print(repr)


def main():
    description = """This utility clones the RT_GROUP_ICON, RT_ICON and RT_VERSION
resource types of two executables."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("source", help="source file")
    parser.add_argument("dest", nargs="?", default="", help="destination file")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose")
    parser.add_argument("--dry-run", action="store_true", help="dry run")
    parser.add_argument(
        "--remove-extra",
        action="store_true",
        help="remove extra resources from destination",
    )
    parser.add_argument(
        "--copy-version", action="store_true", help="include version resource"
    )
    args = parser.parse_args()

    if args.dest:
        clone_file(args.source, args.dest, args)
        if args.verbose:
            print("Success!")
        return 0

    else:
        describe_file(args.source, args)
        return 0


if __name__ == "__main__":
    sys.exit(main())
