This dir mirrors files for building various BleachBit packages
using Open Build Service (OBS).

https://en.opensuse.org/openSUSE:Build_Service_Debian_builds

The OBS project page with build status and packages.

https://build.opensuse.org/package/show/home:andrew_z/bleachbit

### Building BleachBit package for Debian/Ubuntu

First install [`osc`](https://github.com/openSUSE/osc) tool.
Then create account on https://build.opensuse.org/ (see
https://github.com/openSUSE/osc/issues/812 for discussion why
login is required).

`osc` command is used to checkout send files to OBS server,
which automatically starts a build on new commits.

```
osc checkout home:andrew_z
cd home:andrew_z
```
