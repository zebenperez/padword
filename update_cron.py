import sys

minute = sys.argv[1]
hour = sys.argv[2].replace("|", "/")
function = sys.argv[3]
project_uuid = sys.argv[4]
path = sys.argv[5]
log = "{}/cron.log".format(path)
#path = "/var/www/django/padword"
#log = "/var/www/django/padword/cron.log"

f = open("{}/padword/cron_settings.py".format(path), "r+")
new_file_text = ""
replace = False
for line in f.readlines():
    if project_uuid in line and function in line:
        new_line = "\t('%s %s * * *', 'padword.cron.%s', [], {'project_uuid': '%s'},'>> %s'),\n" % (minute, hour, function, project_uuid, log)
        if minute != "-1" and "-1" not in hour:
            new_file_text += new_line
        replace = True
    else:
        if line == "]\n" and replace == False:
            new_line = "\t('%s %s * * *', 'padword.cron.%s', [], {'project_uuid': '%s'},'>> %s'),\n]\n" % (minute, hour, function, project_uuid, log)
            new_file_text += new_line
        else:
            new_file_text += "{}".format(line)

#f_out = open("{}/padword/cron_settings_temp.py".format(path), "w")
f.seek(0)
f.write(new_file_text)
f.truncate()
f.close()

