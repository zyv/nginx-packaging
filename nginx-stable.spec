%define nginx_user      nginx
%define nginx_group     %{nginx_user}
%define nginx_home      %{_localstatedir}/lib/nginx
%define nginx_home_tmp  %{nginx_home}/tmp
%define nginx_logdir    %{_localstatedir}/log/nginx
%define nginx_confdir   %{_sysconfdir}/nginx
%define nginx_datadir   %{_datadir}/nginx
%define nginx_webroot   %{nginx_datadir}/html
%define real_name       nginx

Name:           nginx-stable
Version:        1.0.6
Release:        1%{?dist}
Summary:        Robust, small and high performance HTTP and reverse proxy server
Group:          System Environment/Daemons   

# BSD License (two clause)
# http://www.freebsd.org/copyright/freebsd-license.html
License:        BSD
URL:            http://nginx.net/
BuildRoot:      %{_tmppath}/%{real_name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:      pcre-devel,zlib-devel,openssl-devel,perl-devel,perl(ExtUtils::Embed)
BuildRequires:      libxslt-devel,gd-devel
Requires:           pcre,openssl,gd
Requires:           perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
# for /usr/sbin/useradd
Requires(pre):      shadow-utils
Requires(post):     chkconfig
# for /sbin/service
Requires(preun):    chkconfig, initscripts
Requires(postun):   initscripts
Provides:           webserver

Source0:    http://nginx.org/download/nginx-%{version}.tar.gz
Source1:    %{real_name}.init
Source2:    %{real_name}.logrotate
Source3:    virtual.conf
Source4:    ssl.conf
Source5:    nginx-upstream-fair.tgz
Source6:    upstream-fair.conf
Source7:    %{real_name}.sysconfig
Source100:  index.html
Source101:  poweredby.png
Source102:  nginx-logo.png
Source103:  50x.html
Source104:  404.html

# removes -Werror in upstream build scripts.  -Werror conflicts with
# -D_FORTIFY_SOURCE=2 causing warnings to turn into errors.
Patch0:     nginx-auto-cc-gcc.patch

# configuration patch to match all the Fedora paths for logs, pid files
# etc.
Patch1:     nginx-config.patch

%description
Nginx [engine x] is an HTTP(S) server, HTTP(S) reverse proxy and IMAP/POP3
proxy server written by Igor Sysoev.

One third party module, nginx-upstream-fair, has been added.

%prep
%setup -q -n %{real_name}-%{version}

%patch0 -p0
%patch1 -p0
%{__tar} zxvf %{SOURCE5}

%build
# nginx does not utilize a standard configure script.  It has its own
# and the standard configure options cause the nginx configure script
# to error out.  This is is also the reason for the DESTDIR environment
# variable.  The configure script(s) have been patched (Patch1 and
# Patch2) in order to support installing into a build environment.
export DESTDIR=%{buildroot}
./configure \
    --user=%{nginx_user} \
    --group=%{nginx_group} \
    --prefix=%{nginx_datadir} \
    --sbin-path=%{_sbindir}/%{real_name} \
    --conf-path=%{nginx_confdir}/%{real_name}.conf \
    --error-log-path=%{nginx_logdir}/error.log \
    --http-log-path=%{nginx_logdir}/access.log \
    --http-client-body-temp-path=%{nginx_home_tmp}/client_body \
    --http-proxy-temp-path=%{nginx_home_tmp}/proxy \
    --http-fastcgi-temp-path=%{nginx_home_tmp}/fastcgi \
    --http-uwsgi-temp-path=%{nginx_home_tmp}/uwsgi \
    --http-scgi-temp-path=%{nginx_home_tmp}/scgi \
    --pid-path=%{_localstatedir}/run/%{real_name}.pid \
    --lock-path=%{_localstatedir}/lock/subsys/%{real_name} \
    --with-http_ssl_module \
    --with-http_realip_module \
    --with-http_addition_module \
    --with-http_xslt_module \
    --with-http_image_filter_module \
    --with-http_sub_module \
    --with-http_dav_module \
    --with-http_flv_module \
    --with-http_gzip_static_module \
    --with-http_random_index_module \
    --with-http_secure_link_module \
    --with-http_degradation_module \
    --with-http_stub_status_module \
    --with-http_perl_module \
    --with-mail \
    --with-mail_ssl_module \
    --with-ipv6 \
    --with-cc-opt="%{optflags} $(pcre-config --cflags)" \
    --add-module=%{_builddir}/nginx-%{version}/nginx-upstream-fair \
    --with-ld-opt="-Wl,-E" # so the perl module finds its symbols

make %{?_smp_mflags} 

# rename the readme for nginx-upstream-fair so it doesn't conflict with the main
# readme
mv nginx-upstream-fair/README nginx-upstream-fair/README.nginx-upstream-fair

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot} INSTALLDIRS=vendor
find %{buildroot} -type f -name .packlist -exec rm -f {} \;
find %{buildroot} -type f -name perllocal.pod -exec rm -f {} \;
find %{buildroot} -type f -empty -exec rm -f {} \;
find %{buildroot} -type f -exec chmod 0644 {} \;
find %{buildroot} -type f -name '*.so' -exec chmod 0755 {} \;
chmod 0755 %{buildroot}%{_sbindir}/nginx
%{__install} -p -D -m 0755 %{SOURCE1} %{buildroot}%{_initrddir}/%{real_name}
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{real_name}
%{__install} -p -D -m 0644 %{SOURCE7} %{buildroot}%{_sysconfdir}/sysconfig/%{real_name}
%{__install} -p -d -m 0755 %{buildroot}%{nginx_confdir}/conf.d
%{__install} -p -m 0644 %{SOURCE3} %{SOURCE4} %{SOURCE6} %{buildroot}%{nginx_confdir}/conf.d
%{__install} -p -d -m 0755 %{buildroot}%{nginx_home_tmp}
%{__install} -p -d -m 0755 %{buildroot}%{nginx_logdir}
%{__install} -p -d -m 0755 %{buildroot}%{nginx_webroot}
%{__install} -p -m 0644 %{SOURCE100} %{SOURCE101} %{SOURCE102} %{SOURCE103} %{SOURCE104} %{buildroot}%{nginx_webroot}

# convert to UTF-8 all files that give warnings.
for textfile in CHANGES
do
    mv $textfile $textfile.old
    iconv --from-code ISO8859-1 --to-code UTF-8 --output $textfile $textfile.old
    rm -f $textfile.old
done

%clean
rm -rf %{buildroot}

%pre
if [ $1 == 1 ]; then
    %{_sbindir}/useradd -c "Nginx user" -s /bin/false -r -d %{nginx_home} %{nginx_user} 2>/dev/null || :
fi

%post
if [ $1 == 1 ]; then
    /sbin/chkconfig --add %{real_name}
fi

%preun
if [ $1 = 0 ]; then
    /sbin/service %{real_name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{real_name}
fi

%postun
if [ $1 == 2 ]; then
    /sbin/service %{real_name} upgrade || :
fi

%files
%defattr(-,root,root,-)
%doc LICENSE CHANGES README nginx-upstream-fair/README.nginx-upstream-fair
%{nginx_datadir}/
%{_sbindir}/%{real_name}
%{_mandir}/man3/%{real_name}.3pm.gz
%{_initrddir}/%{real_name}
%dir %{nginx_confdir}
%dir %{nginx_confdir}/conf.d
%config(noreplace) %{nginx_confdir}/conf.d/*.conf
%config(noreplace) %{nginx_confdir}/win-utf
%config(noreplace) %{nginx_confdir}/%{real_name}.conf.default
%config(noreplace) %{nginx_confdir}/mime.types.default
%config(noreplace) %{nginx_confdir}/fastcgi_params
%config(noreplace) %{nginx_confdir}/fastcgi_params.default
%config(noreplace) %{nginx_confdir}/fastcgi.conf
%config(noreplace) %{nginx_confdir}/fastcgi.conf.default
%config(noreplace) %{nginx_confdir}/scgi_params
%config(noreplace) %{nginx_confdir}/scgi_params.default
%config(noreplace) %{nginx_confdir}/uwsgi_params
%config(noreplace) %{nginx_confdir}/uwsgi_params.default
%config(noreplace) %{nginx_confdir}/koi-win
%config(noreplace) %{nginx_confdir}/koi-utf
%config(noreplace) %{nginx_confdir}/%{real_name}.conf
%config(noreplace) %{nginx_confdir}/mime.types
%config(noreplace) %{_sysconfdir}/logrotate.d/%{real_name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{real_name}
%dir %{perl_vendorarch}/auto/%{real_name}
%{perl_vendorarch}/%{real_name}.pm
%{perl_vendorarch}/auto/%{real_name}/%{real_name}.so
%attr(-,%{nginx_user},%{nginx_group}) %dir %{nginx_home}
%attr(-,%{nginx_user},%{nginx_group}) %dir %{nginx_home_tmp}
%attr(-,%{nginx_user},%{nginx_group}) %dir %{nginx_logdir}


%changelog
* Wed Sep 01 2011 Denis Frolov <d.frolov81 at mail dot ru> - 1.0.6-1
- rebuild to 1.0.6

* Wed Jul 20 2011 Denis Frolov <d.frolov81 at mail dot ru> - 1.0.5-1
- rebuild to 1.0.5

* Sat Jun 05 2011 Denis Frolov <d.frolov81 at mail dot ru> - 1.0.4-1
- rebuild to 1.0.4

* Tue May 26 2011 Denis Frolov <d.frolov81 at mail dot ru> - 1.0.3-1
- rebuild to 1.0.3

* Wed May 11 2011 Denis Frolov <d.frolov81 at mail dot ru> - 1.0.2-1
- rebuild to 1.0.2

* Sun May 10 2011 Denis Frolov <d.frolov81 at mail dot ru> - 1.0.1-1
- rebuild to 1.0.1

* Wed Dec 15 2010 Denis Frolov <d.frolov81 at mail dot ru> - 0.8.54-1
- rebuild to 0.8.54

* Thu Nov 30 2010 Denis Frolov <d.frolov81 at mail dot ru> - 0.8.53-1
- rebuild to 0.8.53

* Wed Jun 16 2010 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.67-1
- rebuild to 0.7.67

* Thu Jun 08 2010 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.66-1
- rebuild to 0.7.66

* Thu Feb 02 2010 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.65-1
- rebuild to 0.7.65

* Thu Nov 17 2009 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.64-1
- rebuild to 0.7.64

* Thu Oct 27 2009 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.63-1
- rebuild to 0.7.63

* Thu Sep 15 2009 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.62-1
- rebuild to 0.7.62

* Mon Jun 22 2009 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.61-1
- rebuild to 0.7.61

* Wed Jun 16 2009 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.60-1
- rebuild to 0.7.60

* Sat Jun 13 2009 Denis Frolov <d.frolov81 at mail dot ru> - 0.7.59-1
- rebuild to 0.7.59

* Thu Feb 19 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.6.35-2
- rebuild

* Thu Feb 19 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.6.35-1
- update to 0.6.35

* Tue Dec 30 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.6.34-1
- update to 0.6.34
- Fix inclusion of /usr/share/nginx tree => no unowned directories [mschwendt]

* Sun Nov 23 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.6.33-1
- update to 0.6.33

* Sun Jul 27 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.6.32-1
- update to 0.6.32
- nginx now supports DESTDIR so removed the patches that enabled it

* Mon May 26 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.6.31-3
- update init script
- remove 'default' listen parameter

* Tue May 13 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.6.31-2
- added missing Source files

* Mon May 12 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.6.31-1
- update to new upstream stable branch 0.6
- added 3rd party module nginx-upstream-fair
- add /etc/nginx/conf.d support [#443280]
- use /etc/sysconfig/nginx to determine nginx.conf [#442708]
- added default webpages
- add Requires for versioned perl (libperl.so) (via Tom "spot" Callaway)
- drop silly file Requires (via Tom "spot" Callaway)

* Sat Jan 19 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.5.35-1
- update to 0.5.35

* Sun Dec 16 2007 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.5.34-1
- update to 0.5.34

* Mon Nov 12 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.33-2
- bump build number - source wasn't update

* Mon Nov 12 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.33-1
* update to 0.5.33

* Mon Sep 24 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.32-1
- updated to 0.5.32
- fixed rpmlint UTF-8 complaints.

* Sat Aug 18 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.31-3
- added --with-http_stub_status_module build option.
- added --with-http_sub_module build option.
- add in pcre-config --cflags

* Sat Aug 18 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.31-2
- remove BuildRequires: perl-devel

* Fri Aug 17 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.31-1
- Update to 0.5.31
- specify license is BSD

* Sat Aug 11 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.30-2
- Add BuildRequires: perl-devel - fixing rawhide build

* Mon Jul 30 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.30-1
- Update to 0.5.30

* Tue Jul 24 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.29-1
- Update to 0.5.29

* Wed Jul 18 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.28-1
- Update to 0.5.28

* Mon Jul 09 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.27-1
- Update to 0.5.27

* Mon Jun 18 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.26-1
- Update to 0.5.26

* Sat Apr 28 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.19-1
- Update to 0.5.19

* Mon Apr 02 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.17-1
- Update to 0.5.17

* Mon Mar 26 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.16-1
- Update to 0.5.16
- add ownership of /usr/share/nginx/html (#233950)

* Fri Mar 23 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.15-3
- fixed package review bugs (#235222) given by ruben@rubenkerkhof.com

* Thu Mar 22 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.15-2
- fixed package review bugs (#233522) given by kevin@tummy.com

* Thu Mar 22 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 0.5.15-1
- create patches to assist with building for Fedora
- initial packaging for Fedora
