# This rpmbuild.spec is designed in particular for OpenSUSE Build Service
# to build packages for CentOS, Fedora, and OpenSUSE.

# The minimum supported Fedora version is now Fedora 30.
# CentOS 7 is supported but CentOS 8 is not because it lacks Python 2.

%if 0%{?fedora}
# Example definition of variable "fedora" on Fedora 31 is "31"
%{!?fedora_version: %define fedora_version %fedora}
%endif

%if 0%{?rhel_version} || 0%{?centos_version} < 800
%define python_bin %{__python}
%endif

%define python_pkg_pre python

%if 0%{?fedora} || 0%{?centos_version} >= 800
# Since Fedora 30, the variable __python refers to Python 3,
# so explicitly use Python 2.
%define python_bin %{__python2}
# In Fedora 30 and CentOS 8, the package prefixes changed from "python" to "python2".
%define python_pkg_pre python2
%endif

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
%{!?python_sitelib: %define python_sitelib %(%{python_bin} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%endif

%if 0%{?suse_version}
%define python_sitelib %py_sitedir
%define python_bin %{__python}
%endif

Name:           bleachbit
Version:        3.1.0
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
BuildRequires:  %{python_pkg_pre}
BuildRequires:  %{python_pkg_pre}-devel
BuildRequires:  %{python_pkg_pre}-setuptools
Requires:       python >= 2.7
Requires:       gtk3
Requires:       usermode
Requires:       %{python_pkg_pre}-chardet
Requires:       %{python_pkg_pre}-gobject
%endif

# CentOS 7 does not have python-scandir, but BleachBit can fall back a
# slower mode without the python-scandir package.
%if 0%{?fedora_version}
Requires:       %{python_pkg_pre}-scandir
%endif

%if 0%{?centos_version} >= 800
BuildRequires:  hostname
%endif

%if 0%{?suse_version}
%if 0%{?suse_version} > 910
BuildRequires:  desktop-file-utils
%endif
BuildRequires:  make
BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  update-desktop-files
Requires:       python-gnome
Requires:       gtk3
Requires:       python-xml
Requires:       python-scandir
Requires:       python-chardet
Requires:       python2-gobject
%py_requires
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
%{python_bin} setup.py build

cp %{name}.desktop %{name}-root.desktop
sed -i -e 's/Name=BleachBit$/Name=BleachBit as Administrator/g' %{name}-root.desktop

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

make install DESTDIR=$RPM_BUILD_ROOT prefix=%{_prefix}

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{name}.desktop

sed -i -e 's/Exec=bleachbit$/Exec=bleachbit-root/g' %{name}-root.desktop

desktop-file-install \
	--dir=%{buildroot}/%{_datadir}/applications/ \
	--vendor="" %{name}-root.desktop

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
sed -i -e 's/^Exec=bleachbit$/Exec=xdg-su -c bleachbit/g' %{name}-root.desktop

desktop-file-install \
	--dir=%{buildroot}/%{_datadir}/applications/ \
	--vendor="" %{name}-root.desktop

%suse_update_desktop_file -i %{name}-root Utility Filesystem
%endif

%if 0%{?suse_version}
%suse_update_desktop_file %{name} Utility Filesystem
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
%{_datadir}/appdata
%{_datadir}/appdata/%{name}.appdata.xml
%{_datadir}/applications/%{name}.desktop
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version} || 0%{?suse_version} >= 1030
%{_datadir}/applications/%{name}-root.desktop
%endif
%{_datadir}/%{name}/
%{_datadir}/pixmaps/%{name}.png
%{_datadir}/polkit-1
%{_datadir}/polkit-1/actions
%{_datadir}/polkit-1/actions/org.bleachbit.policy




%changelog
