:: Build vcpkg gtk3+introspection build for PyGObject
::
:: This script should be executed in the vcpkg root
vcpkg install gtk3[introspection]:x86-windows librsvg:x86-windows
vcpkg install gtk3[introspection]:x64-windows librsvg:x64-windows
cd installed
zip -X -r gtk3.24-x86-windows.zip x86-windows -x x86-windows\debug\*
zip -X -r gtk3.24-x86-windows-debug.zip x86-windows\debug
zip -X -r gtk3.24-x64-windows.zip x64-windows -x x64-windows\debug\*
zip -X -r gtk3.24-x64-windows-debug.zip x64-windows\debug
cd ..
