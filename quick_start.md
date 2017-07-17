# Quick Start

## 1.Setup Development Environment

To setup development enviroment for this web project, follow below steps:

- Clone this project and cd to pgscm folder

```bash
$ git clone https://github.com/hieulq/pgscm
```

- Create python virtual environment and use created virtualenv as source

```bash
$ virtualenv -p python3 venv
$ . venv/bin/activate
```

- Install dependencies package using pip

```bash
(venv)$ pip install -U -r requirements.txt 

```

- Install docker CE engine: [https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#install-from-a-package](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#install-from-a-package)

- Run mariadb container:

```bash
$ sudo docker run -p 3306:3306 --name mariadb_pgscm -e MYSQL_ROOT_PASSWORD=pgscm -d mariadb
# container_id output here
```

- Run phpmyadmin container:

```bash
$ sudo docker run --name myadmin -d --link mariadb_pgscm:db -p 8080:80 phpmyadmin/phpmyadmin
# container_id output here
```

- Access **mariadb_pgscm** container and create **pgscm** databases with password is **pgscm**

```bash
$ sudo  docker exec -it mariadbtest bash
root@container_id:/# mysql -uroot -ppgscm
Welcome to the MariaDB monitor.  Commands end with ; or \g.
Your MariaDB connection id is 9
Server version: 10.2.7-MariaDB-10.2.7+maria~jessie mariadb.org binary distribution

Copyright (c) 2000, 2017, Oracle, MariaDB Corporation Ab and others.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

MariaDB [(none)]> 
...

CREATE DATABASE pgscm;
GRANT ALL PRIVILEGES ON pgscm.* TO 'root'@'localhost' \
  IDENTIFIED BY 'pgscm';

GRANT ALL PRIVILEGES ON pgscm.* TO 'root'@'%' \
  IDENTIFIED BY 'pgscm';
exit

```

- Logout to mariadb console anh logout **mariadb_pgscm** container 

- Verify db_config in ```config.py``` file

```py
class DevelopmentConfig(Config):
    DEBUG = True
...
    SQLALCHEMY_DATABASE_URI = \
        'mysql+pymysql://root:pgscm@localhost:3306/pgscm'
```

- Populate the pgscm database

```bash
(venv)$ python manage.py db upgrade
```

- Run webserver to verify

```bash
$ python manage.py runserver
```