from boaz import *
import pytest
import pytest_html
import time
from pymemcache.client import base
from pymemcache import serde
import time
import hashlib
import mysql.connector
#import memcache
#import memcache.serverHashFunction = adler32


"""
Caching
https://memcached.org/about
Memcached has share-nothing architecture & is easy to scale
allows for distributed caching

In this assignment:

localhost is our server to store the results 
for sample APIs in RAM

1) want to avoid recomputing data
2) want to avoid accessing a slow data store


Implement a simple caching layer (redis, Memcached, etc..) 
for a simple network service (web, database, etc..)
E.g. https (Links to an external site.)://github.com/memcached/memcached/wiki/ 
(Links to an external site.)Programming (Links to an external site.)
Show your work with test cases showing the cache in operation
"""
class TestMemcache(BoazBase):
    """
    Test Cases for avoiding recomputing data
    # """
    def setup_class(self):
        """
        Set up: connect client to server
        """
        self.mc = base.Client(('localhost', 11211),
                              serializer=serde.python_memcache_serializer,
                              deserializer=serde.python_memcache_deserializer)

    def teardown_class(self):
        """
        close client & flush cache
        """
        self.mc.close()
        self.mc.flush_all()

    def test_verify_fibonacci(self):
        """
        Test Fibonacci with first 20 fibonacci numbers
        """
        fib_nums = BoazBase.get_test_data()
        computations = len(fib_nums)
        # nothing in the cache 1st run
        for key, expected in fib_nums.items():
            actual = BoazBase.fibonacci_with_cache(key, self.mc)
            assert actual == expected
        # everything is in the cache
        for key, expected in fib_nums.items():
            actual = BoazBase.fibonacci_with_cache(key, self.mc)
            assert actual == expected
        self.mc.flush_all()

    def test_performance_fibonacci(self):
        """
        Test Fibonacci with first 20 fibonacci numbers
        """
        fib_nums = BoazBase.get_test_data()
        computations = len(fib_nums)
        start_time = time.perf_counter_ns()
        # nothing in the cache 1st run
        for key, expected in fib_nums.items():
            actual = BoazBase.fibonacci_with_cache(key, self.mc)
        end_time = time.perf_counter_ns()
        BoazBase.print_time("\nFibonacci without memcached", computations, end_time - start_time)
        # everything is in the cache
        start_time = time.perf_counter_ns()
        for key, expected in fib_nums.items():
            actual = BoazBase.fibonacci_with_cache(key, self.mc)
        end_time = time.perf_counter_ns()
        BoazBase.print_time("\nFibonacci with memcached", computations, end_time - start_time)
        self.mc.flush_all()

    def test_content_access(self):
        """
        Test access content from hard disk vs cache
        Applies to cache versus web content & database store
        """
        # test without memcached -- load from hard disk
        trials = BoazBase.get_trial_size()
        content = BoazBase.get_content_file()
        start_time = time.perf_counter_ns()
        for i in range(0, trials):
            fd = open(content, "rb")
            fd.read()  # read from disk
        end_time = time.perf_counter_ns()
        BoazBase.print_time("\nContent from HD", trials, end_time - start_time)
        # load content from cache
        self.mc.flush_all()
        key = str(int(hashlib.sha3_224(content.encode('utf-8')).hexdigest()[:5],16)).encode('utf-8')
        fd = open(content, "rb")
        bytes = fd.read()  # read from disk once
        self.mc.set(key, bytes)  # store bytes in cache
        start_time = time.perf_counter_ns()
        for i in range(0, trials):
            self.mc.get(key) # read from cache
        end_time = time.perf_counter_ns()
        BoazBase.print_time("\nContent from Cache", trials, end_time - start_time)
        fd.close()

    def test_memcache_with_mysql(self):
        """
        Same concept as previous test:
        Access cache vs. a slow data store
        https://dev.mysql.com/doc/refman/5.6/en/ha-memcached-mysql-frontend.html
        https://downloads.mysql.com/docs/mysql-memcached-en.pdf
        https://dev.mysql.com/doc/mysql-ha-scalability/en/ha-memcached-interfaces-python.html
        Test using truncated sample hashes
        """
        login = BoazBase.get_mysql_credentials()
        cnx = mysql.connector.connect(user=login['username'],
                                      password=login['password'],
                                      host='127.0.0.1')
        cursor = cnx.cursor()
        BoazBase.create_db(cnx, cursor)
        use_db = "USE {} ".format(TestData.DB_NAME) + ";"
        cursor.execute(use_db)
        BoazBase.create_table(cursor)
        #insert data--
        BoazBase.insert_into_db_table(cnx, cursor)
        # query data without from mysql db ---
        query = ("SELECT run, sha3_256, sha3_384, sha3_512 FROM " + TestData.table_name)
        start_time = time.perf_counter_ns()
        cursor.execute(query)
        end_time = time.perf_counter_ns()
        db_access_time = end_time-start_time
        # socket objects not serilizable, use tuple
        values = [(run, sha3_256, sha3_384, sha3_512) for (run, sha3_256, sha3_384, sha3_512) in cursor]
        # for (run, sha3_256, sha3_384, sha3_512) in values:
        #     print("Run {} sha3_256 {} sha3_384 {} sha3_512 {}".format(run, sha3_256, sha3_384, sha3_512))
        key = str(int(hashlib.sha3_224(TestData.DB_NAME.encode('utf-8')).hexdigest()[:5],16)).encode('utf-8')
        self.mc.flush_all()
        self.mc.set(key, values)
        # query data from cache ---
        start_time = time.perf_counter_ns()
        c_val = self.mc.get(key)
        end_time = time.perf_counter_ns()
        # for (run, sha3_256, sha3_384, sha3_512) in c_val:
        #     print("Run {} sha3_256 {} sha3_384 {} sha3_512 {}".format(run, sha3_256, sha3_384, sha3_512))
        BoazBase.print_time("\nAccess MySQL db query: ",TestData.db_records, db_access_time)
        BoazBase.print_time("\nAccess cache: ", TestData.db_records, end_time - start_time)
        BoazBase.drop_table(cursor)
        BoazBase.drop_db(cursor)
        cnx.close()
