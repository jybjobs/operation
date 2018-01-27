# keepalived 

## 一、 什么是keepalived？
Keepalived是一个用C语言编写的路由软件。该项目的主要目标是为Linux系统和基于Linux的基础设施提供简单而强大的负载均衡和高可用性设施。Loadbalancing框架依赖于众所周知的广泛使用的Linux虚拟服务器（IPVS） 内核模块来提供Layer4负载平衡。Keepalived实现了一组检查器，根据其健康动态地自适应维护和管理负载均衡服务器池。另一方面，VRRP实现高可用性 协议。VRRP是路由器故障转移的根本障碍。另外，Keepalived在VRRP有限状态机上实现了一系列钩子，提供低级和高速的协议交互。Keepalived框架可以独立使用，也可以一起使用，以提供弹性基础设施。
（来源：[keepalived官网](http://www.keepalived.org)）


## 二、 keepalived工作原理

![Atomic Elements](http://www.keepalived.org/doc/_images/software_design.png)

keepalived是以VRRP协议为实现基础的，VRRP全称Virtual Router Redundancy Protocol，即[虚拟路由冗余协议](http://en.wikipedia.org/wiki/VRRP)。

虚拟路由冗余协议，可以认为是实现路由器高可用的协议，即将N台提供相同功能的路由器组成一个路由器组，这个组里面有一个master和多个backup，master上面有一个对外提供服务的vip（该路由器所在局域网内其他机器的默认路由为该vip），master会发组播，当backup收不到vrrp包时就认为master宕掉了，这时就需要根据VRRP的优先级来选举一个backup当master。这样的话就可以保证路由器的高可用了。

keepalived主要有三个模块，分别是core、check和vrrp。core模块为keepalived的核心，负责主进程的启动、维护以及全局配置文件的加载和解析。check负责健康检查，包括常见的各种检查方式。vrrp模块是来实现VRRP协议的。

## 三、 安装（centos为例）
 keepalived源码包下载地址：http://www.keepalived.org/download.html
由于Keepalived官方不提供任何Linux发行包，只提供源代码和代码库，所有需要编译安装(当然yum、apt-get 也有提供源)。

#### 1、yum install -y openssl-devel popt-devel

#### 2、编译
```
wget http://www.keepalived.org/software/keepalived-1.2.13.tar.gz
tar zxvf keepalived-1.2.13.tar.gz 
cd keepalived-1.2.13
./configure --prefix=/usr/local/keepalived
make && make install

注意：如果多处安装，可以打包可执行文件到新环境直接安装。
cd /usr/local/ && tar zcvf keepalived-bin-1.2.13.tar.gz ./keepalived
```

#### 3、安装
```
#! /bin/bash
wget http://192.168.70.56/keepalived/keepalived-bin-1.2.13.tar.gz
tar zxvf keepalived-bin-1.2.13.tar.gz
cp ./keepalived/sbin/keepalived /usr/sbin/
cp ./keepalived/etc/sysconfig/keepalived /etc/sysconfig/
cp ./keepalived/etc/rc.d/init.d/keepalived /etc/init.d/
cd /etc/init.d/
chkconfig --add keepalived
chkconfig keepalived on
mkdir -p /etc/keepalived
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
echo "net.ipv4.ip_nonlocal_bind = 1" >> /etc/sysctl.conf
sysctl -p /etc/sysctl.conf
```

#### 4、配置
```
echo "
! Configuration File for keepalived
global_defs { # 全局配置
    router_id app_ka_1
}
vrrp_script chk_app {
    script "/etc/keepalived/checkMySQL.py -h 127.0.0.1 -P 3306"
    interval 15
}
vrrp_instance VI_KA_1 {
    state BACKUP # MASTER/BACKUP
    nopreempt
    interface eth0  #网卡
    virtual_router_id 23  # 指定实例所属的VRRP路由器ID
    priority 100 #优先级
    advert_int 5 #以秒为单位指定广播时间间隔

    # 单播配置
    unicast_src_ip 192.168.110.136 #本地IP
    unicast_peer {
         192.168.110.140 #远端IP
    }
    authentication { #认证
        auth_type PASS
        auth_pass 1111
    }
    track_script {
        chk_app
    }
    virtual_ipaddress { ＃VIP定义块，限制为20个IP地址
        192.168.110.200 #vip
    }
    notify_master #指定在转换到主状态期间执行的shell脚本
    notify_backup #指定在转换到备份状态期间执行的shell脚本

}
" >/etc/keepalived/keepalived.conf
```
#### 5.测试
 注意：防火墙一定要开启 vrrp协议的支持，（端口 112）


## 四、 keepalived命令行参数：

    -f，-use-file = FILE
    使用指定的配置文件。默认配置文件是“/etc/keepalived/keepalived.conf”。
    -P，-vrrp
    只运行VRRP子系统。这对于不使用IPVS负载均衡器的配置很有用。
    -C，  –check
    只运行健康检查子系统。这对于使用IPVS负载平衡器和单个控制器进行故障切换的配置非常有用。
    -l，-log-console
    将消息记录到本地控制台。默认行为是将消息记录到syslog。
    -D，-log-detail
    详细的日志消息。
    -S，-log-facility = [0-7]
    将syslog工具设置为LOG_LOCAL [0-7]。默认的系统日志工具是LOG_DAEMON。
    -V，-dont-release-vrrp
    不要在守护进程中删除VRRP VIP和VROUTE。默认行为是当keepalived退出时删除所有的VIP和VROUTE
    -I，-dont-release-ipvs
    守护进程停止时不要删除IPVS拓扑。它是在keepalived退出时从IPVS虚拟服务器表中删除所有条目的默认行为。
    -R，–dont-respawn
    不要重新生成子进程。默认行为是如果任一进程退出，则重新启动VRRP和检查器进程。
    -n，-dont-fork
    不要分解守护进程。这个选项会导致keepalived在前台运行。
    -d，-dump-conf
    转储配置数据。
    -p，-pid = FILE
    为父保持进程使用指定的pidfile。keepalived的默认pid文件是“/var/run/keepalived.pid”。
    -r，-vrrp_pid = FILE
    为VRRP子进程使用指定的pidfile。VRRP子进程的默认pid文件是“/var/run/keepalived_vrrp.pid”。
    -c，-checkers_pid = FILE
    检查器子进程使用指定的pidfile。检查器子进程的默认pid文件是“/var/run/keepalived_checkers.pid”。
    -x，-snmp
    启用S​​NMP子系统。
    -v，-version
    显示版本并退出。
    -h，-help
    显示此帮助信息并退出。
