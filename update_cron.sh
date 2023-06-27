HOUR=$1
MIN=$2
FUNCTION=$3
PROJECT=$4
PATH=/var/www/django/padword
SYSPATH=/opt/envs/padword/bin
FILENAME="$PATH/padword/cron_settings.py"

/usr/bin/sed -i "s/\(.*('\).* \* \* \*'\(.*\)$FUNCTION\(.*\): '.*'}\(.*\)/\1$MIN $HOUR * * *'\2$FUNCTION\3: '$PROJECT'}\4/" $FILENAME
/usr/bin/sed -i "s/|/\//" $FILENAME

/usr/bin/sleep 3

source /opt/envs/padword/bin/activate
$SYSPATH/python $PATH/manage.py crontab remove  
$SYSPATH/python $PATH/manage.py crontab add 
#/opt/envs/padword/bin/python /var/www/django/padword/manage.py crontab remove >> /var/www/django/padword/kk.log 
#/opt/envs/padword/bin/python /var/www/django/padword/manage.py crontab add >> /var/www/django/padword/kk1.log
