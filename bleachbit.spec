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

# 2025-03-15
#  openSUSE:Slowroll reports suse_version=1699
#  openSUSE:Tumbleweed reports suse_version=1699
#  CentOS_9_Stream reports centos_version=900
#  Fedora 41 reports fedora_version=41


%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version} || 0%{?almalinux_version} || 0%{?rocky_version}
%define is_redhat_family 1
%else
%define is_redhat_family 0
%endif

%if 0%{?is_opensuse}
%define pyprefix %{primary_python}
%endif

%if !0%{?is_opensuse} && !%{is_redhat_family}
%{error:This package is only for openSUSE or Red Hat family distributions}
%endif

%if 0%{?almalinux_version}
%define has_fdupes 0
%else
%define has_fdupes 1
%endif

# Fedora 42 unified /usr/sbin https://fedoraproject.org/wiki/Changes/Unify_bin_and_sbin
%if "%{_bindir}" == "%{_sbindir}"
%define has_sbin 0
%else
%define has_sbin 1
%endif

Name:           bleachbit
Version:        5.0.1
Release:        1%{?dist}
Summary:        Remove unnecessary files, free space, and maintain privacy
License:        GPL-3.0-or-later
URL:            https://www.bleachbit.org
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

%if %{is_redhat_family}
BuildRequires:  desktop-file-utils
BuildRequires:  gettext
BuildRequires:  python3-chardet
BuildRequires:  python3-psutil
BuildRequires:  python3-setuptools
Requires(post): desktop-file-utils
Requires(postun): desktop-file-utils
Requires:       python3
Requires:       gtk3
Requires:       python3-chardet
Requires:       python3-gobject
Requires:       python3-psutil
%endif

%if 0%{?is_opensuse}
BuildRequires:  desktop-file-utils
BuildRequires:  make
BuildRequires:  openSUSE-release
BuildRequires:  %{pyprefix}
BuildRequires:  python-rpm-macros
BuildRequires:  %{pyprefix}-chardet
BuildRequires:  %{pyprefix}-psutil
BuildRequires:  %{pyprefix}-setuptools
BuildRequires:  %{pyprefix}-sqlite-utils
BuildRequires:  %{pyprefix}-xml
BuildRequires:  update-desktop-files
Requires:       gobject-introspection
Requires:	    %{pyprefix}
Requires:       %{pyprefix}-chardet
Requires:       %{pyprefix}-gobject
Requires:       %{pyprefix}-gobject-Gdk
Requires:       %{pyprefix}-psutil
Requires:       %{pyprefix}-sqlite-utils
Requires:       %{pyprefix}-xml
Requires:		openSUSE-release
Requires:       typelib(Gtk)
Requires:       typelib(Notify)
Requires:       xdg-utils
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
python3 -V
%{__python3} -V


%build
%{__python3} setup.py build
cp org.bleachbit.BleachBit.desktop org.bleachbit.BleachBit-root.desktop
sed -i -e 's/Name=BleachBit$/Name=BleachBit as Administrator/g' org.bleachbit.BleachBit-root.desktop

%if %{is_redhat_family}

cat > bleachbit.pam <<EOF
#%%PAM-1.0
auth		include		config-util
account		include		config-util
session		include		config-util
EOF

cat > bleachbit.console <<EOF
USER=root
PROGRAM=/usr/bin/bleachbit
SESSION=true
EOF

%endif

make delete_windows_files


%install
make install PYTHON=%{__python3} DESTDIR=%{buildroot} prefix=%{_prefix}

%if %{is_redhat_family}

sed -i -e 's/Exec=bleachbit$/Exec=bleachbit-root/g' org.bleachbit.BleachBit-root.desktop

desktop-file-install \
	--dir=%{buildroot}/%{_datadir}/applications/ \
	--vendor="" org.bleachbit.BleachBit-root.desktop

# consolehelper and userhelper
ln -s consolehelper %{buildroot}/%{_bindir}/%{name}-root
%if %{has_sbin}
mkdir -p %{buildroot}/%{_sbindir}
ln -s ../..%{_bindir}/%{name} %{buildroot}/%{_sbindir}/%{name}-root
%endif
mkdir -p %{buildroot}%{_sysconfdir}/pam.d
install -m 644 %{name}.pam %{buildroot}%{_sysconfdir}/pam.d/%{name}-root
mkdir -p %{buildroot}%{_sysconfdir}/security/console.apps
install -m 644 %{name}.console %{buildroot}%{_sysconfdir}/security/console.apps/%{name}-root

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
python3 bleachbit.py --sysinfo
python3 bleachbit.py -l | wc -l
python3 bleachbit.py -p system.cache | wc -l
python3 -m unittest -v tests.TestFileUtilities tests.TestUnix


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
%if %{is_redhat_family}
%config(noreplace) %{_sysconfdir}/pam.d/%{name}-root
%config(noreplace) %{_sysconfdir}/security/console.apps/%{name}-root
%{_bindir}/%{name}-root
%if %{has_sbin}
%{_sbindir}/%{name}-root
%endif
%endif
%{_bindir}/%{name}
%{_datadir}/metainfo/org.bleachbit.BleachBit.metainfo.xml
%{_datadir}/applications/org.bleachbit.BleachBit.desktop
%{_datadir}/applications/org.bleachbit.BleachBit-root.desktop
%{_datadir}/%{name}/
%{_datadir}/pixmaps/%{name}.png
%{_datadir}/pixmaps/%{name}-indicator.svg
%dir %{_datadir}/polkit-1
%dir %{_datadir}/polkit-1/actions
%{_datadir}/polkit-1/actions/org.bleachbit.policy


%changelog

* Tue Mar 18 2025 Andrew Ziem <andrew@bleachbit.org> - 5.0.1-1
- Update to 5.0.1
- See https://www.bleachbit.org/news
