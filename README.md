pyres is a simple Python tool and module for copying resources in windows executables.

pyres currently acts as a command line utility which clones the RT_GROUP_ICON, RT_ICON and optionally RT_VERSION resource types betweeb executables.

The goal of the project is to develop more capabilities for the module, such as adding/replacing icons and a set/get interface for resource strings.

Example run:
```
py pyres.py from.exe to.exe --verbose --remove-extra

Cloning resources [14, 3] from 'from.exe' to 'to.exe'
source:
(14, 123, 1033): b'\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x01\x00 \x00\x1f\xb2\x00\x00\x01\x00'... (20 bytes)
(3, 1, 1033): b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00'... (45599 bytes)
destination:
(3, 1, 1033): b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00'... (13584 bytes)
(3, 2, 1033): b'(\x00\x00\x00\x80\x00\x00\x00\x00\x01\x00\x00\x01\x00 \x00\x00\x00\x00\x00'... (67624 bytes)
(3, 3, 1033): b'(\x00\x00\x00`\x00\x00\x00\xc0\x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00'... (38056 bytes)
(3, 4, 1033): b'(\x00\x00\x000\x00\x00\x00`\x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00'... (9640 bytes)
(3, 5, 1033): b'(\x00\x00\x00 \x00\x00\x00@\x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00'... (4264 bytes)
(3, 6, 1033): b'(\x00\x00\x00\x18\x00\x00\x000\x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00'... (2440 bytes)
(3, 7, 1033): b'(\x00\x00\x00\x10\x00\x00\x00 \x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00'... (1128 bytes)
identical resources in source and dest: set()
extra resources in destination: {(14, 'APP_ICON', 1033), (3, 2, 1033), (3, 4, 1033), (3, 7, 1033), (3, 5, 1033), (3, 3, 1033), (3, 6, 1033)}
Updating with 'to.exe' with:
(3, 1, 1033): b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00'... (45599 bytes)
(14, 'APP_ICON', 1033): None
(3, 2, 1033): None
(3, 4, 1033): None
(3, 7, 1033): None
(3, 5, 1033): None
(3, 3, 1033): None
(3, 6, 1033): None
Success!
```
