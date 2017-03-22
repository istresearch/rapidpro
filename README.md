[![Coverage Status](https://coveralls.io/repos/github/rapidpro/rapidpro/badge.svg?branch=master)](https://coveralls.io/github/rapidpro/rapidpro?branch=master) 

# RapidPro     

RapidPro is a hosted service for visually building interactive messaging applications.
To learn more, please visit the project site at http://rapidpro.github.io/rapidpro.

### Get Involved

To run RapidPro for development, follow the Quick Start guide at http://rapidpro.github.io/rapidpro/docs/development.

### License

In late 2014, Nyaruka partnered with UNICEF to expand on the capabilities of TextIt and release the source code as RapidPro under the Affero GPL (AGPL) license.

In brief, the Affero license states you can use the RapidPro source for any project free of charge, but that any changes you make to the source code must be available to others. Note that unlike the GPL, the AGPL requires these changes to be made public even if you do not redistribute them. If you host a version of RapidPro, you must make the same source you are hosting available for others.

RapidPro has dual copyright holders of UNICEF and Nyaruka.

### IST Research Fork

This fork was created as a space in which to build experimental prototypes of new RapidPro features, with the intent of eventually contributing these back to the RapidPro codebase. To obtain views of both this fork and the original repository, use the following commands.

```
git clone git+ssh://git@github.com/istresearch/rapidpro ./rapidpro/
cd rapidpro
git remote add -m rapidpro-master rapidpro git://github.com/rapidpro/rapidpro
```

### Ubuntu Setup Instructions

To get RapidPro working on your own system, execute the following steps.

1. Install PostgreSQL and its additional components.
    
    ```
    > sudo apt-get update
    > sudo apt-get install postgresql postgresql-contrib postgresql-server-dev-9.3 python-psycopg2 postgis postgresql-9.3-postgis-2.1
    ```
    
2. Configure PostgreSQL to allow local socket connections.
    
    ```
    > sudo vi /etc/postgresql/9.3/main/pg_hba.conf
    ```
    
    ```
    # "local" is for Unix domain socket connections only
    local   all             all                                     md5
    ```
    
3. Install NodeJS and related components. Note that the lines that display version information below are for illustrative purposes only; the versions you actually get may be higher.
    
    ```
    > curl -sL https://deb.nodesource.com/setup_7.x | sudo -E bash -
    > sudo apt-get install nodejs
    > node --version
    v7.4.0
    > which npm
    /usr/bin/npm
    > sudo npm install -g less
    > sudo npm install -g coffee-script
    > sudo npm install -g bower
    ```

4. Install Redis.

    ```
    > cd /opt
    > wget http://download.redis.io/releases/redis-3.2.6.tar.gz
    > tar zxf redis-3.2.6.tar.gz
    > cd redis-3.2.6/
    > make
    ```
    
5. Set up the `temba` user in PostgreSQL.

    ```
    > sudo -u postgres createuser temba --pwprompt -d
    Enter password for new role:
    Enter it again:
    > sudo -u postgres psql --user=temba -W postgres
    Password for user temba:
    psql (9.3.15)
    Type "help" for help.
    
    
    postgres=> create database temba ;
    CREATE DATABASE
    postgres=> \q
    
    > sudo -u postgres psql
    psql (9.3.15)
    Type "help" for help.
    
    postgres=# \c temba ;
    You are now connected to database "temba" as user "postgres".
    temba=# create extension postgis ;
    CREATE EXTENSION
    temba=# create extension postgis_topology ;
    CREATE EXTENSION
    temba=# create extension hstore ;
    CREATE EXTENSION
    temba=# \q
    ```

6. Install Python. If your system did not come with at least Python 2.7.9 (Ubuntu 14.04 comes with Python 2.7.6), then you might want to upgrade to avoid some warnings raised by RapidPro. Once the proper Python version is installed, ensure that `pip` and `virtualenv` are also installed.
    
    ```
    > sudo apt-get update
    > sudo apt-get install python-pip
    > sudo pip install virtualenv
    ```

7. Install the `ncurses` library.
    
    ```
    > sudo apt-get update
    > sudo apt-get install libncurses5-dev libncursesw5-dev
    ```

8. Install RapidPro. (If you have already cloned the repository to your development environment, then skip the first three commands, which will clone it to `/opt/`.)

    ```
    > cd /opt/
    > mkdir istresearch ; cd istresearch
    > git clone git+ssh://git@github.com/istresearch/rapidpro ./rapidpro/
    > cd rapidpro/temba
    > cp settings.py.dev settings.py.local
    > ln -s settings.py.local settings.py
    > cd ..
    > virtualenv -p /usr/local/bin/python2.7 rapidpro-env
    > source rapidpro-env/bin/activate
    env> pip install -r pip-freeze.txt
    env> pip install requests[security]
    env> python manage.py migrate
    env> bower install
    env> deactivate
    ```

9. Configure the RapidPro server. Edit `temba/settings.py.local` file (which is ignored by `.gitignore`) with the following:
    * Set `HOSTNAME` and `TEMBA_HOST` with the hostname of your server box.
    * In the `DATABASES` JSON object, ensure that the `NAME`, `USER`, and `PASSWORD` match the values for the `temba` user created in step 5.
    * Add custom settings:
        
        ```
        ALLOWED_HOSTS = [ '*' ]
        MAGE_AUTH_TOKEN = 'foo'
        MAGE_API_URL = 'http://localhost:8026/api/v1'
        ```
        
### Starting the RapidPro Server

```
> sudo service postgresql start
> /opt/redis-3.2.6/src/redis-server &
> cd /opt/nyaruka/rapidpro/
> source rapidpro-env/bin/activate
env> python manage.py runserver 0.0.0.0:8000
```

This will start the RapidPro server on the local box, accessible in a browser as http://localhost:8000.

