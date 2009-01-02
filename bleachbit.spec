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
Version:        0.2.1
Release:        1%{?dist}
Summary:        Remove unnecessary files, free space, and maintain privacy

%if 0%{?mandriva_version}
Group:          File tools
%else
Group:          Applications/System
%endif
License:        GPLv3
URL:            http://bleachbit.sourceforge.net
Source0:        %{name}-%{version}.tar.bz2
%if 0%{?mandriva_version}
BuildRoot:      %{_tmppath}/%{name}-%{version}
%else
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
%endif

BuildArch:      noarch

%if 0%{?mandriva_version}
BuildRequires:  libpython2.5-devel
Requires:       gnome-python
Requires:       gnome-python-gnomevfs
Requires:       pygtk2.0 >= 2.6
Requires(post): desktop-file-utils
Requires(postun): desktop-file-utils
%endif

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
BuildRequires:  desktop-file-utils
BuildRequires:  python-devel
Requires:       gnome-python2-gnomevfs
Requires:       pygtk2 >= 2.6
%endif

%if 0%{?suse_version}
BuildRequires:  python-devel
BuildRequires:  update-desktop-files
Requires:       python-gnome
Requires:       python-gtk >= 2.6
%endif

Requires:       python >= 2.4


%description
BleachBit removes unnecessary files, frees space, and maintains your
privacy.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT

%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{name}.desktop
%endif

%if 0%{?mandriva_version}
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
dir -d %{buildroot}%{py_platsitedir}/%{name}
%python_compile_opt
%python_compile
install *.pyc *.pyo %{buildroot}%{py_platsitedir}/%{name}
%endif

%if 0%{?suse_version}
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT --prefix /usr/
%suse_update_desktop_file %{name}
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
%doc COPYING
%if 0%{?mandriva_version}
%{py_platsitedir}/%{name}-*egg-info
%{py_platsitedir}/%{name}/*.py
%{py_platsitedir}/%{name}/*.pyc
%{py_platsitedir}/%{name}/*.pyo
%else
%{python_sitelib}/*
%endif
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop




%changelog
