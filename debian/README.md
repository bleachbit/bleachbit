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

`osc` command is used to checkout and send files to OBS server,
which automatically starts a build on new commit.

##### Checkout files from OBS and compare to this directory
```bash
osc checkout home:andrew_z bleachbit -o /tmp/obsfiles
diff -u3 /tmp/obsfiles .
```
Checkout syntax is `osc co <project> <package> --outdir <path>`.

###### Make a local build
From the `osc` checkout execute
```bash
osc build xUbuntu_20.10
```
where `xUbuntu_20.10` is a custom name for one of the configured
repositories.

##### Branch/fork OBS package for testing builds on OBS
```bash
$ osc branch home:andrew_z bleachbit
A working copy of the branched package can be checked out with:

osc co home:abitrolly:branches:home:andrew_z/bleachbit
```

##### Inspect build status with `osc results` and `osc buildlog`
```bash
$ osc results
xUbuntu_20.10        x86_64     failed
xUbuntu_20.04        x86_64     succeeded*
xUbuntu_18.04        x86_64     succeeded*
...
$ osc buildlod xUbuntu_20.10
...

[   97s] [   83.277694] reboot: Power down
[   97s] ### VM INTERACTION END ###
[   97s]
[   97s] cloud132 failed "build bleachbit.dsc" at Sat Nov 28 17:44:06 UTC 2020.
[   97s]
```

More commands in
[`osc` cheatsheet](https://en.opensuse.org/images/d/df/Obs-cheat-sheet.pdf)
