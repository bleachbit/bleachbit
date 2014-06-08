%if 0%{?fedora}
# FC9 doesn't define 'fedora_version' but apparently OpenSUSE Build Service's FC9 does
%{!?fedora_version: %define fedora_version %fedora}
%endif

%if 0%{?mdkver}
# Mandriva 2009 doesn't define 'mandriva_version' but apparently OpenSUSE Build Service's MDK2009 does
%{!?mandriva_version: %define mandriva_version %(echo %{mdkver} | grep -o ^2...)}
%endif


%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%endif

%if 0%{?mandriva_version}
%define python_compile_opt python -O -c "import compileall; compileall.compile_dir('.')"
%define python_compile     python -c "import compileall; compileall.compile_dir('.')"
%endif

%if 0%{?suse_version}
%define python_sitelib %py_sitedir
%endif

Name:           bleachbit
Version:        1.2
Release:        1%{?dist}
Summary:        Remove unnecessary files, free space, and maintain privacy

%if 0%{?mandriva_version}
Group:          File tools
%else
Group:          Applications/System
%endif
License:        GPLv3
URL:            http://bleachbit.sourceforge.net
Source0:        %{name}-%{version}.tar.gz
%if 0%{?mandriva_version}
BuildRoot:      %{_tmppath}/%{name}-%{version}
%else
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
%endif

BuildArch:      noarch

%if 0%{?mandriva_version}
BuildRequires:  desktop-file-utils
%if 0%{?mandriva_version} >= 200910
BuildRequires:  libpython2.6-devel
%else
BuildRequires:  libpython2.5-devel
%endif
Requires:       gnome-python
Requires:       gnome-python-gnomevfs
Requires:       pygtk2 >= 2.6
Requires:       pygtk2.0 >= 2.6
Requires:       python-simplejson
Requires:       usermode-consoleonly
Requires(post): desktop-file-utils
Requires(postun): desktop-file-utils
%endif

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
BuildRequires:  desktop-file-utils
BuildRequires:  gettext
BuildRequires:  python-devel
Requires:       python >= 2.5
Requires:       gnome-python2-gnomevfs
Requires:       pygtk2 >= 2.6
Requires:       python-simplejson
Requires:       usermode
%endif

%if 0%{?suse_version}
%if 0%{?suse_version} > 910
BuildRequires:  desktop-file-utils
%endif
BuildRequires:  make
BuildRequires:  python-devel
BuildRequires:  update-desktop-files
Requires:       python-gnome
Requires:       python-gtk >= 2.6
Requires:       python-simplejson
Requires:       python-xml
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
%{__python} setup.py build

cp %{name}.desktop %{name}-root.desktop
sed -i -e 's/Name=BleachBit$/Name=BleachBit as Administrator/g' %{name}-root.desktop

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version} || 0%{?mandriva_version}

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

# remove Windows-specific cleaners
grep -l os=.windows. cleaners/*xml | xargs rm -f
# remove Windows-specific modules
rm -f bleachbit/Windows.py

%if 0%{?rhel_version} || 0%{?centos_version}
echo WARNING: translations not supported on CentOS 5.0 and RHEL 5.0 because of old msgfmt
rm -f po/*.po
%endif


%install
rm -rf $RPM_BUILD_ROOT

make install DESTDIR=$RPM_BUILD_ROOT prefix=%{_prefix}

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version} || 0%{?mandriva_version}
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

%if 0%{?rhel_version} || 0%{?centos_version}
echo WARNING: translations not supported on CentOS 5.0 and RHEL 5.0 because of old msgfmt
echo > %{name}.lang
%else
make -C po install DESTDIR=$RPM_BUILD_ROOT
%find_lang %{name}
%endif


%clean
rm -rf $RPM_BUILD_ROOT

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
%post
update-desktop-database &> /dev/null ||:

%postun
update-desktop-database &> /dev/null ||:
%endif

%if 0%{?mandriva_version}
%post
%{update_menus}
%{update_desktop_database}

%postun
%{clean_menus}
%{clean_desktop_database}
%endif



%files -f %{name}.lang
%defattr(-,root,root,-)
%doc COPYING README
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version} || 0%{?mandriva_version}
%config(noreplace) %{_sysconfdir}/pam.d/%{name}-root
%config(noreplace) %{_sysconfdir}/security/console.apps/%{name}-root
%{_bindir}/%{name}-root
%{_sbindir}/%{name}-root
%endif
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version} || 0%{?mandriva_version} ||  0%{?suse_version} >= 1030
%{_datadir}/applications/%{name}-root.desktop
%endif
%{_datadir}/%{name}/
%{_datadir}/pixmaps/%{name}.png




%changelog
