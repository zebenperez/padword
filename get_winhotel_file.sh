DATE=$(date "+%Y%m%d")
FILENAME="_Products_07__TPV_HIGO.CSV"
FULLNAME="$DATE$FILENAME"
wget --user=L0F98HH --password='P00IkMMhs!2' ftp://51.38.104.89/$FULLNAME
rm media/*.CSV
mv $FULLNAME media/

