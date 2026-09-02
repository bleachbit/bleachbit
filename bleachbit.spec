# This rpmbuild.spec is designed for the OpenSUSE Build Service
# to build packages for CentOS, Fedora, and OpenSUSE.

# Fedora docs deprecate:
#  * Group
#  * BuildRoot
#  * %clean
# https://docs.fedoraproject.org/en-US/packaging-guidelines/

# openSUSE docs deprecate:
#  * Group
#  * %clean
# https://en.opensuse.org/openSUSE:Specfile_guidelines

# Standard macro definitions on OBS.
#  openSUSE:Leap:15.6 reports suse_version 1500
#  openSUSE:Leap:16.0 reports suse_version 1600
#  openSUSE:Slowroll reports suse_version=1699
#  openSUSE:Tumbleweed reports suse_version=1699
#  CentOS_9_Stream reports centos_version=900
#  Fedora 41 reports fedora_version=41

%define pyexe %{__python3}

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version} || 0%{?almalinux_version} || 0%{?rocky_version}
%define is_redhat_family 1
%else
%define is_redhat_family 0
%endif

%if 0%{?is_opensuse}
%define pyprefix %{modern_python}
%define is_leap 0
%if 0%{?suse_version} <= 1600
%define is_leap 1
%endif # suse_version <= 1600
%if 0%{?suse_version} == 1500
%define pyexe /usr/bin/python3.11
%endif # suse_version == 1500
%endif # is_opensuse

%if !0%{?is_opensuse} && !%{is_redhat_family}
%{error:This package is only for openSUSE or Red Hat family distributions}
%endif

%if 0%{?almalinux_version}
%define has_fdupes 0
%else
%define has_fdupes 1
%endif

Name:           bleachbit
Version:        6.0.3
Release:        1%{?dist}
Summary:        Remove unnecessary files, free space, and maintain privacy
License:        GPL-3.0-or-later
URL:            https://www.bleachbit.org
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

%if %{is_redhat_family}
BuildRequires:  desktop-file-utils
BuildRequires:  gettext
BuildRequires:  python3-psutil
BuildRequires:  python3-requests
BuildRequires:  python3-setuptools
Requires(post): desktop-file-utils
Requires(postun): desktop-file-utils
Requires:       python3
Requires:       gtk3
Requires:       python3-gobject
Requires:       python3-psutil
Requires:       python3-requests
Requires:       polkit
%endif

%if 0%{?is_opensuse}
BuildRequires:  desktop-file-utils
BuildRequires:  make
BuildRequires:  %{pyprefix}
BuildRequires:  python-rpm-macros
BuildRequires:  %{pyprefix}-base
# Leap 16.0 split the unversioned /usr/bin/python3 symlink into a separate
# python3-base package that is no longer pulled in transitively by
# python313-base. Require it explicitly so %{__python3} resolves.
%if 0%{?suse_version} == 1600
BuildRequires:  python3-base
%endif
BuildRequires:  %{pyprefix}-psutil
BuildRequires:  %{pyprefix}-requests
BuildRequires:  %{pyprefix}-setuptools
%if ! %{is_leap}
BuildRequires:  %{pyprefix}-sqlite-utils
%endif
BuildRequires:  %{pyprefix}-xml
BuildRequires:  update-desktop-files
Requires:       gobject-introspection
Requires:       %{pyprefix}
Requires:       %{pyprefix}-gobject
Requires:       %{pyprefix}-gobject-Gdk
Requires:       %{pyprefix}-psutil
Requires:       %{pyprefix}-requests
%if ! %{is_leap}
Requires:       %{pyprefix}-sqlite-utils
%endif
Requires:       %{pyprefix}-xml
Requires:       typelib(Gtk) = 3.0
Requires:       typelib(Notify)
Requires:       xdg-utils
Recommends:     libayatana-appindicator3-1
%endif

%if %{has_fdupes}
BuildRequires:  fdupes
%endif

%description
BleachBit frees disk space and maintains privacy by quickly removing
unnecessary files such as cache, cookies, browser history, temporary
files, and system logs. It can also shred files  and clean free disk
space to prevent data recovery.

%prep
%setup -q
%{pyexe} -V


%build
%{pyexe} setup.py build
cp org.bleachbit.BleachBit.desktop org.bleachbit.BleachBit-root.desktop
sed -i -e 's/Name=BleachBit$/Name=BleachBit as Administrator/g' org.bleachbit.BleachBit-root.desktop

make delete_windows_files


%install
make install PYTHON=%{pyexe} DESTDIR=%{buildroot} prefix=%{_prefix}

%if %{is_redhat_family}

sed -i -e 's/^Exec=bleachbit$/Exec=pkexec bleachbit/g' org.bleachbit.BleachBit-root.desktop

desktop-file-install \
    --dir=%{buildroot}/%{_datadir}/applications/ \
    --vendor="" org.bleachbit.BleachBit-root.desktop

%endif


%if 0%{?is_opensuse}
sed -i -e 's/^Exec=bleachbit$/Exec=xdg-su -c bleachbit/g' org.bleachbit.BleachBit-root.desktop

desktop-file-install \
    --dir=%{buildroot}/%{_datadir}/applications/ \
    --vendor="" org.bleachbit.BleachBit-root.desktop

%suse_update_desktop_file -i org.bleachbit.BleachBit-root Utility Filesystem

%suse_update_desktop_file org.bleachbit.BleachBit Utility Filesystem
%endif

desktop-file-validate %{buildroot}/%{_datadir}/applications/org.bleachbit.BleachBit.desktop
desktop-file-validate %{buildroot}/%{_datadir}/applications/org.bleachbit.BleachBit-root.desktop

make -C po install DESTDIR=%{buildroot}
%find_lang %{name}

%if %{has_fdupes}
# Make symlinks for redundant .pyc files.
%fdupes -s %{buildroot}
%endif


%check
%{pyexe} bleachbit.py --sysinfo
%{pyexe} bleachbit.py -l | wc -l
%{pyexe} bleachbit.py -p system.cache | wc -l
%{pyexe} -m unittest -v tests.TestFileUtilities tests.TestUnix


%if %{is_redhat_family}
%post
update-desktop-database &> /dev/null ||:

%postun
update-desktop-database &> /dev/null ||:
%endif


%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README.md
%license COPYING
%{_bindir}/%{name}
%{_datadir}/metainfo/org.bleachbit.BleachBit.metainfo.xml
%{_datadir}/applications/org.bleachbit.BleachBit.desktop
%{_datadir}/applications/org.bleachbit.BleachBit-root.desktop
%{_datadir}/%{name}/
%{_datadir}/pixmaps/%{name}.png
%dir %{_datadir}/polkit-1
%dir %{_datadir}/polkit-1/actions
%{_datadir}/polkit-1/actions/org.bleachbit.policy


%changelog

* Tue Mar 18 2025 Andrew Ziem <andrew@bleachbit.org> - 6.0.3-1
- Update to 6.0.3
- See https://www.bleachbit.org/news
