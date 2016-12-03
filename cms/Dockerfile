from dockerfiles/centos-lamp
MAINTAINER yubingJin jinyubing@yihecloud.com
RUN yum -y install php-mbstring
RUN echo "extension=mbstring.so" >> /etc/php.ini
ADD crm.zip /var/www/html
RUN cd /var/www/html && unzip -o crm.zip && rm -rf crm.zip
RUN chmod -R 777 /var/www/html
