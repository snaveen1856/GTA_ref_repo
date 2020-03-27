"""
This module is responsible for check disk utilization,
If disk utilization reaches 90% then deletes the 2 years old data from the server.
In case disk usage reaches 90% and there were no 2 years old files found.
then script will delete old files to free up disk space up to 80%.
"""
import os
def disk_usage():
    """
    it returns the disk usage in percentage
    """
    op=os.popen("df / | awk '{print $5}' | tail -1").read()
    return int(op.split('%')[0])
if disk_usage() >= 90:
    if os.popen("find /var/www/html/sutas-logs/.* -type f -mtime +730 -exec ls -l {} \;").read():
	os.system("find /var/www/html/sutas-logs/.* -type f -mtime +730 -exec rm -rf {} \;")
if disk_usage() >=90:
    while True:
	ls=os.popen("find /var/www/html/sutas-logs/.* -type f -mtime +365 -exec ls -r {} \;").read()
	lis=ls.split('\n')
	for i in lis[-100:]:
	    os.system("rm -f "+i)
	if disk_usage() <80 or os.popen("find "\
	"/var/www/html/sutas-logs/.* -type f -mtime +365 -exec ls -l {} \;").read():
	    break
else:
    print("disk limit not yet reached")

