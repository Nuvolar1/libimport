import logging
import sqlite3
import mysql.connector
from mysql.connector import errorcode


class Database:

    def __init__(self, host, username, password, database=None):
        self.host = host
        self.database = database
        self.password = password
        self.username = username
        self.connection = mysql.connector.connect(host=host, username=username, password=password)
        cursor = self.connection.cursor(buffered=True)
        if not self.exists(database):
            cursor.execute("CREATE DATABASE {}".format(database))
            self.connection.commit()
        else:
            self.connection.close()
            self.connection = mysql.connector.connect(host=host, username=username, password=password, database=database)
        # self.connection.row_factory = sqlite3.Row

    def init_new_connection(self):
        return mysql.connector.connect(host=self.host, username=self.username, password=self.password, database=self.database)

    def exists(self, database_name):
        cursor = self.connection.cursor(buffered=True, dictionary=True)
        try:
            cursor.execute("SHOW DATABASES")
            for x in cursor:
                if database_name in str(x.values()):
                    return True
            return False
        except Exception as e:
            logging.error(e)

    def create(self):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(
                "CREATE TABLE categories( "
                "nome varchar(255) not null, "
                "codice varchar(255) not null, "
                "codicepadre varchar(255), "
                "wcpid int null, "
                "wcid int, "
                "primary key(codice,codicepadre,wcid)"
                ")"
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                logging.info("already exists.")
            else:
                logging.error(err.msg)
        try:
            cursor.execute('''CREATE TABLE products(
            nome text not null,
            codice varchar(255) not null,
            codicecategoria varchar(255) not null,
            wcid int not null,
            wccid int null,
            hash char(32),
            primary key(codice, codicecategoria, wcid))''')
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                logging.info("already exists.")
            else:
                logging.error(err.msg)
        try:
            cursor.execute('''CREATE TABLE variations(
            nome text not null,
            codice varchar(255) not null,
            codicepadre varchar(255) not null,
            wcpid int not null,
            wcid int not null,
            hash char(32),
            primary key(codice, wcpid, wcid))''')
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                logging.info("already exists.")
            else:
                logging.error(err.msg)

    def add_categories(self, categories):
        cursor = self.connection.cursor(buffered=True)
        for category in categories:
            try:
                logging.info("saving category:" + category.nome)
                cursor.execute("INSERT INTO categories (NOME,CODICE,CODICEPADRE,WCPID,WCID) VALUES (%s, "
                               "%s, %s, %s, %s)", (category.nome, category.codice,
                                                   category.codice_padre,
                                                   None if category.wcpid is None else category.wcpid,
                                                   None if category.wcid is None else category.wcid))
                self.connection.commit()
            except sqlite3.IntegrityError as e:
                logging.warning(e)

    def add_products(self, products):
        cursor = self.connection.cursor(buffered=True)
        for product in products:
            try:
                logging.info("saving product:" + product.nome)
                cursor.execute("INSERT INTO products (NOME,CODICE,CODICECATEGORIA,WCID,WCCID,HASH) VALUES (%s, "
                               "%s, %s, %s, %s, %s)", (product.nome, product.codice,
                                                       product.codice_categoria, product.wcid, product.wccid,
                                                       str(product.md5hash())))
                self.connection.commit()
            except sqlite3.IntegrityError as e:
                logging.warning(e)

    def add_variations(self, variations):
        cursor = self.connection.cursor(buffered=True)
        for variation in variations:
            try:
                logging.info("saving variation:" + variation.nome)
                cursor.execute(
                    "INSERT INTO variations (NOME,CODICE,CODICEPADRE,WCPID,WCID,HASH) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        variation.nome, variation.codice, variation.codice_padre, variation.wcpid, variation.wcid,
                        str(variation.md5hash())))
                self.connection.commit()
            except sqlite3.IntegrityError as e:
                logging.warning(e)

    def add_product(self, product):
        self.add_products([product])

    def add_category(self, category):
        self.add_categories([category])

    def add_variation(self, variation):
        self.add_variations([variation])

    def update_categories(self, categories):
        cursor = self.connection.cursor(buffered=True)
        for category in categories:
            if category.wcid is None:
                logging.info("updating category: " + str(category.nome))
                cursor.execute(
                    "update categories set nome = %s, wcpid = %s where codice = %s", (category.nome, category.wcpid, category.codice))
                self.connection.commit()
            else:
                matches = []
                for row in self.get_category(category):
                    matches.append(row)
                if matches:
                    logging.info("updating category: " + str(category.nome))
                    cursor.execute(
                        "update categories set nome = %s, wcpid = %s where wcid = %s", (category.nome, category.wcpid, category.wcid))
                    self.connection.commit()
                else:
                    self.add_category(category)

    def update_products(self, products):
        cursor = self.connection.cursor(buffered=True)
        for product in products:
            if product.wcid is None:
                logging.info("updating product: " + str(product.codice))
                cursor.execute(
                    "update products set nome = %s, hash = %s where codice = %s",
                    (product.nome, str(product.md5hash()), product.codice))
                self.connection.commit()
            else:
                matches = []
                for row in self.get_product(product):
                    matches.append(row)
                if matches:
                    logging.info("updating product: " + str(product.codice))
                    cursor.execute(
                        "update products set nome = %s, hash = %s where wcid = %s",
                        (product.nome, str(product.md5hash()), product.wcid))
                    self.connection.commit()
                else:
                    self.add_product(product)

    def update_variations(self, variations):
        cursor = self.connection.cursor(buffered=True)
        for variation in variations:
            if variation.wcid is None:
                logging.info("updating variation 1: " + str(variation.codice))
                cursor.execute(
                    "update variations set nome = %s, hash = %s where codice = %s and codicepadre = %s",
                    (variation.nome, str(variation.md5hash()), variation.codice, variation.codice_padre))
                self.connection.commit()
            else:
                matches = []
                for row in self.get_variation(variation):
                    matches.append(row)
                if matches:
                    logging.info("updating variation 2: " + str(variation.codice))
                    cursor.execute(
                        "update variations set nome = %s, hash = %s where wcid = %s and codicepadre = %s",
                        (variation.nome, str(variation.md5hash()), variation.wcid, variation.codice_padre))
                    self.connection.commit()
                else:
                    self.add_variation(variation)

    def update_product(self, product):
        self.update_products([product])

    def update_category(self, category):
        self.update_categories([category])

    def update_variation(self, variation):
        self.update_variations([variation])

    def get_category(self, category):
        cursor = self.connection.cursor(buffered=True, dictionary=True)
        cursor.execute("select * from categories where codice = %s", (category.codice,))
        for row in cursor.fetchall():
            yield row

    def get_product(self, product):
        cursor = self.connection.cursor(buffered=True, dictionary=True)
        cursor.execute("select * from products where codice = %s", (product.codice,))
        for row in cursor.fetchall():
            yield row

    def get_variation(self, variation):
        cursor = self.connection.cursor(buffered=True, dictionary=True)
        cursor.execute("select * from variations where codice = %s and codicepadre = %s", (variation.codice, variation.codice_padre))
        for row in cursor.fetchall():
            yield row

    def cerca_codice(self, codice):
        rows = []
        cursor = self.connection.cursor(buffered=True, dictionary=True)
        cursor.execute("select * from categories where CODICE = %s", (codice,))
        for row in cursor.fetchall():
            rows.append(row)
        cursor.execute("select * from products where CODICE = %s", (codice,))
        for row in cursor.fetchall():
            rows.append(row)
        cursor.execute("select * from variations where CODICE = %s", (codice,))
        for row in cursor.fetchall():
            rows.append(row)
        return rows

    def close(self):
        self.connection.close()
