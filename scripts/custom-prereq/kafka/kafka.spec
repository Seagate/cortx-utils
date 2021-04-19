%undefine _disable_source_fetch
%define _prefix /opt

Name:           kafka
Version:        %{_kafka_version}_%{_kafka_release}
Release:        %{?dist:el7}
Summary:        Apache Kafka is publish-subscribe messaging rethought as a distributed commit log.

Group:          Applications
License:        Apache License, Version 2.0
URL:            https://kafka.apache.org/
Source0:	kafka_%{_kafka_version}-%{_kafka_release}.tgz
Source1:	kafka.service
Source2:	kafka-zookeeper.service
Requires:	java-1.8.0-openjdk-headless

%description
Kafka is designed to allow a single cluster to serve as the central data backbone for a large organization. It can be elastically and transparently expanded without downtime. Data streams are partitioned and spread over a cluster of machines to allow data streams larger than the capability of any single machine and to allow clusters of co-ordinated consumers. Messages are persisted on disk and replicated within the cluster to prevent data loss.

%global debug_package %{nil}

%prep
%setup -n kafka_%{_kafka_version}-%{_kafka_release}

%build
rm -f libs/{kafka_*-javadoc.jar,kafka_*-scaladoc.jar,kafka_*-sources.jar,*.asc}

%install
mkdir -p $RPM_BUILD_ROOT%{_prefix}/kafka
mkdir $RPM_BUILD_ROOT%{_prefix}/kafka/bin
cp bin/*.sh $RPM_BUILD_ROOT%{_prefix}/kafka/bin/
cp -r libs $RPM_BUILD_ROOT%{_prefix}/kafka/
cp -r config $RPM_BUILD_ROOT%{_prefix}/kafka/
mkdir -p $RPM_BUILD_ROOT/var/log/kafka

mkdir -p $RPM_BUILD_ROOT/etc/systemd/system/
install -m 755 %{S:1} $RPM_BUILD_ROOT/etc/systemd/system/kafka.service
install -m 755 %{S:2} $RPM_BUILD_ROOT/etc/systemd/system/kafka-zookeeper.service

%clean
rm -rf $RPM_BUILD_ROOT

%pre
/usr/bin/getent group kafka >/dev/null || /usr/sbin/groupadd -r kafka
if ! /usr/bin/getent passwd kafka >/dev/null ; then
    /usr/sbin/useradd -r -g kafka -m -d %{_prefix}/kafka -s /sbin/nologin -c "Kafka" kafka
fi

%files
%defattr(-,root,root)
%attr(0755,kafka,kafka) %dir /opt/kafka
%attr(0755,kafka,kafka) /opt/kafka/bin
%attr(0755,kafka,kafka) /opt/kafka/libs
%config(noreplace) %attr(755,kafka,kafka) /opt/kafka/config
%attr(0755,kafka,kafka) %dir /var/log/kafka
%attr(0775,root,kafka) /etc/systemd/system/kafka.service
%attr(0775,root,kafka) /etc/systemd/system/kafka-zookeeper.service

%changelog
