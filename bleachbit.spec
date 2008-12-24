%if 0%{?suse_version}
%define python_sitelib %py_sitedir
%else
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%endif

Name:           bleachbit
Version:        0.1.1
Release:        1%{?dist}
Summary:        Remove unnecessary files, free space, and maintain privacy

Group:          Applications/System
License:        GPLv3
URL:            http://bleachbit.sourceforge.net
Source0:        %{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel

%if 0%{?suse_version}
BuildRequires: update-desktop-files
%endif



%description
BleachBit removes unnecessary files, frees space, and maintains your
privacy.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%if 0%{?suse_version}
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT --prefix /usr/
%suse_update_desktop_file %{name}
%else
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
%endif


%clean
rm -rf $RPM_BUILD_ROOT


%post
%if 0%{?mandriva_version}
%update_menus
%update_desktop_database
%endif
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
update-desktop-database &> /dev/null ||:
%endif


%postun
%if 0%{?mandriva_version}
%clean_menus
%update_desktop_database
%endif
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
%update_desktop-database &> /dev/null ||:
%endif


%files
%defattr(-,root,root,-)
%doc COPYING
%{python_sitelib}/*
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop


%changelog
