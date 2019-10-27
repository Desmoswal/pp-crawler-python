import urllib.request
import urllib.parse
import re
import time
import pika
import multiprocessing


url = "http://hu.kristof.wtf/maildir/"
forbiddenNames = ["Name", "Size", "Last modified", "Description", "Parent Directory"]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

def list_dir(dir):
    req = urllib.request.Request(dir)
    path = req.full_url
    resp = urllib.request.urlopen(req)
    html = resp.read()
    strhtml = html.decode()
    results = re.findall("<a href=\".*\">(?P<name>.*)</a>", strhtml)

    dirlist = []

    for result in results:
        if result not in forbiddenNames:
            dirlist.append(path+result)

    #dirlist = [results for results in results if results not in forbiddenNames]
    #print(dirlist)

    return dirlist

def fill_queue(dirlist, q):
    while dirlist:
        queueitem = dirlist.pop()
        #print("ADDED ITEM: " + queueitem)
        q.put(queueitem)
        #print("append")
        #print(q.qsize())

def scan_directory(dirlist):
    for dir in dirlist:
        #print("DIR:" + dir)
        if dir.endswith('.'):
            #print("FILE FOUND: " + dir)
            channel.basic_publish(exchange='', routing_key='task_queue', body=dir)
        elif dir.endswith('/'):
            #print("DIRECTORY FOUND: " + dir)
            scan_directory(list_dir(dir))

startTime = time.time()
#list_dir(url)

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    q = manager.Queue()

    fill_queue(list_dir(url), q)
    while q.empty() is False:
        #print("WHILE")
        #print("uj process")
        item = q.get()
        p = multiprocessing.Process(target=scan_directory, args=(list_dir(item),))
        #print("uj item: " + item)
        #print("scanning" + item)
        #scan_directory(item)
        p.start()
        p.join()
        p.terminate()
        #print(q.qsize())

    print("finished in : {}".format(time.time() - startTime))