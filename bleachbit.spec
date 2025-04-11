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

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
%define is_redhat_family 1
%else
%define is_redhat_family 0
%endif

%if 0%{?is_opensuse}
%define pyprefix %{primary_python}
%endif

Name:           bleachbit
Version:        4.9.2
Release:        1%{?dist}
Summary:        Remove unnecessary files, free space, and maintain privacy
License:        GPL-3.0-or-later
URL:            https://www.bleachbit.org
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

%if %{is_redhat_family}
BuildRequires:  desktop-file-utils
BuildRequires:  fdupes
BuildRequires:  gettext
BuildRequires:  python3-chardet
BuildRequires:  python3-psutil
BuildRequires:  python3-setuptools
Requires:       python3
Requires:       gtk3
Requires:       usermode
Requires:       python3-chardet
Requires:       python3-gobject
Requires:       python3-psutil
%endif

%if 0%{?is_opensuse}
BuildRequires:  desktop-file-utils
BuildRequires:  fdupes
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



%description
Delete traces of your activities and other junk files to free disk
space and maintain privacy.  BleachBit identifies and erases
broken menu entries, cache, cookies, localizations, recent document
lists, and temporary files in Firefox, Google Chrome, Flash, and 60
other applications.

Shred files to prevent recovery, and wipe free disk space to
hide previously deleted files.


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
make install PYTHON=%{__python3} DESTDIR=$RPM_BUILD_ROOT prefix=%{_prefix}

desktop-file-validate %{buildroot}/%{_datadir}/applications/org.bleachbit.BleachBit.desktop

%if %{is_redhat_family}

sed -i -e 's/Exec=bleachbit$/Exec=bleachbit-root/g' org.bleachbit.BleachBit-root.desktop

desktop-file-install \
	--dir=%{buildroot}/%{_datadir}/applications/ \
	--vendor="" org.bleachbit.BleachBit-root.desktop

# consolehelper and userhelper
ln -s consolehelper %{buildroot}/%{_bindir}/%{name}-root
mkdir -p %{buildroot}/%{_sbindir}
ln -s ../..%{_bindir}/%{name} %{buildroot}/%{_sbindir}/%{name}-root
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

make -C po install DESTDIR=$RPM_BUILD_ROOT
%find_lang %{name}

# Make symlinks for redundant .pyc files.
%fdupes -s %{buildroot}


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
%{_sbindir}/%{name}-root
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

* Tue Mar 18 2025 Andrew Ziem <andrew@bleachbit.org> - 4.9.2-1
- Update to 4.9.2
- See https://www.bleachbit.org/news

