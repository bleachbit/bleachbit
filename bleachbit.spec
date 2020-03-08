# This rpmbuild.spec is designed in particular for OpenSUSE Build Service
# to build packages for CentOS, Fedora, and OpenSUSE.

# The minimum supported Fedora version is now Fedora 30.

%if 0%{?fedora}
# Example definition of variable "fedora" on Fedora 31 is "31"
%{!?fedora_version: %define fedora_version %fedora}
%endif

Name:           bleachbit
Version:        3.9.0
Release:        1%{?dist}
Summary:        Remove unnecessary files, free space, and maintain privacy

Group:          Applications/System
License:        GPLv3
URL:            https://www.bleachbit.org
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-build

BuildArch:      noarch

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
BuildRequires:  desktop-file-utils
BuildRequires:  gettext
%if 0%{?centos_version}
%if 0%{?centos_version} < 800
BuildRequires:  python3-rpm-macros
%endif
%endif
BuildRequires:  python3-setuptools
Requires:       python3
Requires:       gtk3
Requires:       usermode
Requires:       python3-chardet
Requires:       python3-gobject
%endif

# For CentOS and Fedora, do not require scandir.
# CentOS 7 has python36-scandir, but it does not need it because it has Python 3.6.
# CentOS 8 does not have a scandir package, but it does not need it because it has Python 3.6.
# Fedora 31 has python3-scandir, but it is not needed because Fedora 31 has Python 3.7.

# OpenSUSE Tumbleweed as of March 2019
# - does not have package python3-gnome
# - has package python3-scandir, but it does not need it because it has Python 3.7
# - package typelib-1_0-Gtk-3_0 fixes "ValueError: Namespace Gtk not available"
%if 0%{?suse_version}
%if 0%{?suse_version} > 910
BuildRequires:  desktop-file-utils
%endif
BuildRequires:  make
BuildRequires:  python-rpm-macros
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  update-desktop-files
Requires:       gtk3
Requires:       python3-chardet
Requires:       python3-gobject-Gdk
Requires:       python3-xml
Requires:       typelib-1_0-Gtk-3_0
#%py3_requires
%if 0%{?suse_version} >= 1030
Requires:       xdg-utils
%endif
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

%build
%{__python3} setup.py build

make downgrade_desktop

cp org.bleachbit.BleachBit.desktop org.bleachbit.BleachBit-root.desktop
sed -i -e 's/Name=BleachBit$/Name=BleachBit as Administrator/g' org.bleachbit.BleachBit-root.desktop

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}

cat > bleachbit.pam <<EOF
#%PAM-1.0
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
rm -rf $RPM_BUILD_ROOT

make install PYTHON=%{__python3} DESTDIR=$RPM_BUILD_ROOT prefix=%{_prefix}

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
desktop-file-validate %{buildroot}/%{_datadir}/applications/org.bleachbit.BleachBit.desktop

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


%if 0%{?suse_version} >= 1030
sed -i -e 's/^Exec=bleachbit$/Exec=xdg-su -c bleachbit/g' org.bleachbit.BleachBit-root.desktop

desktop-file-install \
	--dir=%{buildroot}/%{_datadir}/applications/ \
	--vendor="" org.bleachbit.BleachBit-root.desktop

%suse_update_desktop_file -i org.bleachbit.BleachBit-root Utility Filesystem
%endif

%if 0%{?suse_version}
%suse_update_desktop_file org.bleachbit.BleachBit Utility Filesystem
%endif

make -C po install DESTDIR=$RPM_BUILD_ROOT
%find_lang %{name}


%clean
rm -rf $RPM_BUILD_ROOT

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
%post
update-desktop-database &> /dev/null ||:

%postun
update-desktop-database &> /dev/null ||:
%endif



%files -f %{name}.lang
%defattr(-,root,root,-)
%doc COPYING README.md CONTRIBUTING.md
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
%config(noreplace) %{_sysconfdir}/pam.d/%{name}-root
%config(noreplace) %{_sysconfdir}/security/console.apps/%{name}-root
%{_bindir}/%{name}-root
%{_sbindir}/%{name}-root
%endif
%{_bindir}/%{name}
%{_datadir}/metainfo
%{_datadir}/metainfo/org.bleachbit.BleachBit.metainfo.xml
%{_datadir}/applications/org.bleachbit.BleachBit.desktop
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version} || 0%{?suse_version} >= 1030
%{_datadir}/applications/org.bleachbit.BleachBit-root.desktop
%endif
%{_datadir}/%{name}/
%{_datadir}/pixmaps/%{name}.png
%{_datadir}/polkit-1
%{_datadir}/polkit-1/actions
%{_datadir}/polkit-1/actions/org.bleachbit.policy




%changelog
