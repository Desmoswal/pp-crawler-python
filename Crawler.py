import urllib.request
import urllib.parse
import re
import time
import pika

url = "http://hu.kristof.wtf/maildir/"
forbiddenNames = ["Name", "Size", "Last modified", "Description", "Parent Directory"]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

queue = []


def list_dir(dir):
    global queue
    req = urllib.request.Request(dir)
    path = req.full_url
    resp = urllib.request.urlopen(req)
    html = resp.read()
    strhtml = html.decode()
    results = re.findall("<a href=\".*\">(?P<name>.*)</a>", strhtml)
    dirlist = [results for results in results if results not in forbiddenNames]

    while dirlist:
        queueitem = path + dirlist.pop()
        #print("ADDED ITEM: " + queueitem)
        queue.append(queueitem)
        #print("append")


def scan_directory(urllist):
    if urllist.endswith('.'):
        print("FILE FOUND: " + urllist)
        channel.basic_publish(exchange='', routing_key='task_queue', body=urllist)
    elif urllist.endswith('/'):
        print("DIRECTORY FOUND: " + urllist)
        list_dir(urllist)


startTime = time.time()
list_dir(url)

while queue:

    item = queue.pop()
    #print("scanning" + item)
    scan_directory(item)

print("finished in : {}".format(time.time() - startTime))