import os
import mysql.connector
from mysql.connector import errorcode


class TestData:

    def init_test_data():
        dir_path = os.path.dirname(os.path.realpath(__file__))
        test_path = str(dir_path) + "/test_input/"
        TestData.fibonacci_input_file = test_path + "test_input.txt"
        TestData.trial_size = test_path + "trials.txt"
        #TestData.content = test_path + "hummingbird.png"
        TestData.mysql = test_path + "mysql_credentials.txt"
        TestData.record_data = test_path + "random.txt"
        TestData.DB_NAME = 'sha3' #lexicon or sample list
        TestData.table_name = 'sample_hashes' #barron's
        TestData.db_records = 20000

class BoazBase:
    """
    BoazBase class for get/set methods to test memcached for:
    1) using cache to avoid recomputation.
    2) database
    3) web content
    """
    TestData.init_test_data()

    @classmethod
    def get_content_file(cls):
        """
        get content file
        :return: file name path
        """
        return TestData.content

    @classmethod
    def get_trial_size(cls):
        """
        read test input data
        """
        with open(TestData.trial_size) as f:
            for line in f:
                trial_size = int(line.rstrip())
        f.close()
        return trial_size

    @classmethod
    def get_mysql_credentials(cls):
        """
        read test input data
        """
        login = {}
        with open(TestData.mysql) as f:
            for line in f:
                if not line.startswith("#"):
                    line.rstrip()
                    tokens = line.split(':')
                    login[tokens[0]] = tokens[1].rstrip()
        f.close()
        return login

    @classmethod
    def get_test_data(cls):
        """
        read test input data
        """
        fib_numbers = {}
        with open(TestData.fibonacci_input_file) as f:
            for line in f:
                if not line.startswith("#"):
                    line.rstrip()
                    tokens = line.split(':')
                    fib_numbers[int(tokens[0])] = int(tokens[1].rstrip())
        f.close()
        return fib_numbers

    @classmethod
    def fibonacci_with_cache(cls, n, mc):
        """
        Iterative Fibonacci

        :param int n
        :param fibonacci number
        """
        result = mc.get(str(n).encode('utf-8'))
        if result:
            return int(result.decode('utf-8'))
        key = n
        curr = 1
        prev = 0
        if n == 0 or n == 1:
            mc.set(str(key).encode('utf-8'), str(n).encode('utf-8'))
            return n
        n = n - 1;
        while n > 0:
            sum = curr + prev
            prev = curr
            curr = sum
            n = n - 1
        mc.set(str(key).encode('utf-8'), str(sum).encode('utf-8'))
        return sum

    @classmethod
    def print_time(cls, describtion, trials, execution_time):
        """
        print time

        :param describtion: method description
        :param trials: computations
        :param time: execution time
        """
        print(describtion + " Avg time " + str(trials/execution_time) + "ns")
        print("for " + str(trials) + " computation(s)/records.")

    @classmethod
    def create_db(cls, cnx, cursor):
        """
        create sample db
        https://dev.mysql.com/doc/connector-python/en/connector-python-example-ddl.html
        """
        try:
            cursor.execute("USE {}".format(TestData.DB_NAME))
        except mysql.connector.Error as err:
            print("Database {} does not exists.".format(TestData.DB_NAME))
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                try:
                    cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(TestData.DB_NAME))
                except mysql.connector.Error as err:
                    print("Failed creating database: {}".format(err))
                    exit(1)
                print("Database {} created successfully.".format(TestData.DB_NAME))
                cnx.database = TestData.DB_NAME
            else:
                print(err)
                exit(1)

    @classmethod
    def create_table(cls, cursor):
        """
        Create table in DB
        :param cursor: cursor obj
        """
        TABLES = {}
        create_table = "CREATE TABLE `" + TestData.table_name + "` ("
        TABLES[TestData.table_name] = (
        "" + create_table + ""
        "  `run` varchar(50) NOT NULL,"
        "  `sha3_256` varchar(100) NOT NULL,"
        "  `sha3_384` varchar(100) NOT NULL,"
        "  `sha3_512` varchar(100) NOT NULL,"
        "  PRIMARY KEY (`run`)"
        ") ENGINE=InnoDB")

        for table_name in TABLES:
            table_description = TABLES[table_name]
            try:
                print("Creating table {}: ".format(table_name), end='')
                cursor.execute(table_description)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
            else:
                print("OK")

    @classmethod
    def insert_into_db_table(cls, cnx, cursor):
        """
        read test input data
        """
        add_member = ("INSERT INTO " + TestData.table_name + ""
                      "(run, sha3_256, sha3_384, sha3_512) "
                      "VALUES (%s, %s, %s, %s)")
        with open(TestData.record_data) as f:
            for line in f:
                line = line.rstrip()
                tokens = line.split(':')
                record_data = (tokens[0], tokens[1], tokens[2], tokens[3])
                cursor.execute(add_member, record_data)
        cnx.commit()
        f.close()

    @classmethod
    def drop_db(cls, cursor):
        """
        drop db
        """
        drop_db_cmd = "DROP DATABASE " + TestData.DB_NAME + ""
        try:
            cursor.execute(drop_db_cmd)
        except mysql.connector.Error as err:
                print("Failed deleting database: {}".format(err))
                exit(1)
        print("Database dropped successfully.")

    @classmethod
    def drop_table(cls, cursor):
        """
        read test input data
        """
        drop_table_cmd = "DROP TABLE " + TestData.table_name
        try:
            cursor.execute(drop_table_cmd)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_UNKNOWN_TABLE:
                print("table does not exist.")
            else:
                print(err.msg)
        else:
            print("Table dropped successfully.")
