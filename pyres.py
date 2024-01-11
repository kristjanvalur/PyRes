# todo: implement http://www.skynet.ie/~caolan/publink/winresdump/winresdump/doc/resfmt.txt

import ctypes
import ctypes.wintypes
import sys
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
    LANGID,
)


kernel32 = ctypes.windll.kernel32

# ctypes functions

prototype = WINFUNCTYPE(HMODULE, LPCWSTR, HANDLE, DWORD)
LoadLibraryEx = prototype(("LoadLibraryExW", kernel32), ((1,), (1,), (1,)))

prototype = WINFUNCTYPE(BOOL, HMODULE)
FreeLibrary = prototype(("FreeLibrary", kernel32), ((1,),))

ENUMRESLANGPROC = ctypes.WINFUNCTYPE(BOOL, HMODULE, LPVOID, LPVOID, WORD, LPVOID)
prototype = WINFUNCTYPE(
    BOOL, HMODULE, LPCWSTR, LPCWSTR, ENUMRESLANGPROC, LPVOID, DWORD, LANGID
)
EnumResourceLanguagesEx = prototype(
    ("EnumResourceLanguagesExW", kernel32), ((1,), (1,), (1,), (1,), (1,), (1,), (1,))
)

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

prototype = WINFUNCTYPE(HRSRC, HMODULE, LPCWSTR, LPCWSTR, WORD)
FindResourceEx = prototype(("FindResourceExW", kernel32), ((1,), (1,), (1,), (1,)))

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

# resource enum
RESOURCE_ENUM_MUI = 0x0002
RESOURCE_ENUM_LN = 0x0001
RESOURCE_ENUM_MUI_SYSTEM = 0x0004
RESOURCE_ENUM_VALIDATE = 0x0008


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


# useful utility functions


def enum_resource_names(hModule, lpType):
    types = []
    cb_error = None

    def callback(hModule, lpType, lpName, lParam):
        try:
            lpType = RESOURCE_PARM(lpType)
            lpName = RESOURCE_PARM(lpName)
            types.append(lpName)
            return True
        except Exception as e:
            nonlocal cb_error
            cb_error = e
            return False

    v = EnumResourceNames(
        hModule,
        RESOURCE_ARG(lpType),
        EnumResourceNameCallback(callback),
        None,
    )
    if cb_error:
        raise cb_error
    if not v:
        raise WinError("EnumResourceNames")

    return types


def enum_resource_languages(hModule, lpType, lpName):
    languages = []
    cb_error = None

    def callback(hModule, lpType, lpName, wLanguage, _):
        try:
            languages.append(wLanguage)
            return True
        except Exception as e:
            nonlocal cb_error
            cb_error = e
            return False

    v = EnumResourceLanguagesEx(
        hModule,
        RESOURCE_ARG(lpType),
        RESOURCE_ARG(lpName),
        ENUMRESLANGPROC(callback),
        None,
        RESOURCE_ENUM_LN,
        0,
    )
    if cb_error:
        raise cb_error
    if not v:
        raise WinError("EnumResourceLanguages")

    return languages


def enum_names_and_languages(hModule, lpType):
    for name in enum_resource_names(hModule, lpType):
        for lang in enum_resource_languages(hModule, lpType, name):
            yield (name, lang)


def enum_all(hModule, types=[]):
    for t in types:
        for name, lang in enum_names_and_languages(hModule, t):
            yield (t, name, lang)


class ResourceEditor(object):
    def __init__(self, filename, args):
        self.filename = filename
        self.args = args

    def update_resources(self, resources):
        with update_resource(self.filename) as update_handle:
            for (type, name, language), data in resources.items():
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

    def load_resource(self, hModule, lpType, lpName, wLanguage=None):
        if wLanguage is None:
            hResource = FindResource(
                hModule, RESOURCE_ARG(lpName), RESOURCE_ARG(lpType)
            )
        else:
            hResource = FindResourceEx(
                hModule,
                RESOURCE_ARG(lpType),
                RESOURCE_ARG(lpName),
                wLanguage,
            )
        if not hResource:
            raise WinError("FindResource")
        size = SizeofResource(hModule, hResource)
        if not size:
            raise WinError("SizeofResource")
        with load_resource(hModule, hResource) as hData:
            ptr = LockResource(hData)
            if not ptr:
                raise WinError("LockResource")
            return ctypes.string_at(ptr, size)

    def get_resources(self, resource_types):
        """Retrieves the manifest(s) embedded in the current executable"""

        with load_library(self.filename) as module:
            manifests = {}
            for res_type, res_name, res_lang in enum_all(module, resource_types):
                v = self.load_resource(module, res_type, res_name, res_lang)
                manifests[(res_type, res_name, res_lang)] = v
            return manifests


def resource_types(args):
    types = [RT_GROUP_ICON, RT_ICON]
    if args.include_version:
        types.append(RT_VERSION)
    return types


def clone_file(source, dest, args):
    re_src = ResourceEditor(source, args)
    re_dst = ResourceEditor(dest, args)

    types = resource_types(args)
    src_resources = re_src.get_resources(types)
    dst_resources = re_dst.get_resources(types)
    if args.verbose:
        print_resource_dict(src_resources, "source")
        print_resource_dict(dst_resources, "destination")

    wrt_resources = src_resources.copy()

    src_res = set(src_resources.keys())
    dst_res = set(dst_resources.keys())

    # find common resource keys in source and dest
    common_res = src_res & dst_res

    # ignore resources which are unchanged
    identical = set()
    for c in common_res:
        if src_resources[c] == dst_resources[c]:
            identical.add(c)
            del wrt_resources[c]
    if args.verbose:
        print(f"identical resources in source and dest: {identical}")

    # find any extra resource keys in the destination
    extra_res = dst_res - src_res
    if args.verbose:
        print(f"extra resources in destination: {extra_res}")

    # remove extra resources in destination
    if args.remove_extra:
        for res in extra_res:
            wrt_resources[res] = None

    if not args.dry_run:
        return re_dst.update_resources(wrt_resources)
    else:
        print("dry run")
        print_resource_dict(wrt_resources, "would update with")


def format_resource_dict(r):
    res = {}
    for k, v in r.items():
        data = "None" if v is None else f"{repr(v[:20])}... ({len(v)} bytes)"
        res[k] = data
    return res


def print_resource_dict(r, header="resources"):
    print(f"{header}:")
    for k, v in format_resource_dict(r).items():
        print(f"{k}: {v}")


def describe_file(source, args):
    re_from = ResourceEditor(source, args)

    resources = re_from.get_resources(resource_types(args))
    print_resource_dict(resources)


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
        "--include-version", action="store_true", help="include version resource"
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
