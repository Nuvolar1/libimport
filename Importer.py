import itertools
import logging

import Database


class Importer:
    def __init__(self, wcapi, host, username, password, database=None):
        self.wcapi = wcapi
        self.database = Database.Database(host, username, password, database)

    def initialize_database(self):
        self.database.create()

    def add_product(self, product):
        self.batch_update_products([product])

    def close_database(self):
        self.database.close()

    def batch_update_products(self, products, batch_max_size=100, force_add=False, force_local=False):
        for i in range(0, len(products), batch_max_size):
            create = []
            update = []
            data = {
                "create": [],
                "update": []
            }
            for product in itertools.islice(products, i, i + batch_max_size):
                if product.wcid is None and not force_add:
                    product.wcid = self.get_id(product, force_local=force_local)
                id_categoria = self.database.cerca_codice(product.codice_categoria)
                if id_categoria:
                    product.wccid = id_categoria[0]['wcid']
                    if product.wcid is None or force_add:
                        create.append(product)
                        data["create"].append(product.get_data())
                    else:
                        hashp = ''
                        for row in self.database.get_product(product): # TODO controllo hash non funzia
                            hashp = str(row['hash'])
                            logging.debug("trovato: "+hashp)
                        logging.debug("Hash database: " + hashp)
                        logging.debug("Hash variante: " + product.md5hash())
                        if str(product.md5hash()) not in hashp:
                            update.append(product)
                            data["update"].append(product.get_data())
                        else:
                            logging.debug("Gia aggiornato: " + str(product))
                else:
                    logging.debug("Skippato: " + str(product))
            try:
                if create or update: # TODO usa data
                    temp = self.wcapi.post("products/batch", data)
                    logging.info(data)
                    logging.info(temp.json())
                    logging.info("status: " + str(temp.status_code))
                    if create:
                        for created, response in zip(create, temp.json()["create"]):
                            created.wcid = response['id']
                    if temp.status_code == 200 or temp.status_code == 201:
                        self.database.update_products(update)
                        self.database.add_products(create)
            except Exception as e:
                logging.warning(e)
            for product in products[i:i+batch_max_size]:
                if product.wcid is not None:
                    self.batch_update_variations(product.get_variations(), product.wcid)

    def batch_update_variations(self, variations, product_id, batch_max_size=100, force_add=False, force_local=False):
        for i in range(0, len(variations), batch_max_size):
            create = []
            update = []
            data = {
                "create": [],
                "update": []
            }
            for variante in itertools.islice(variations, i, i + batch_max_size):
                if variante.wcid is None and not force_add:
                    variante.wcid = self.get_id(variante, force_local=force_local)
                    variante.wcpid = int(product_id)
                if variante.wcid is None or force_add:
                    create.append(variante)
                    data["create"].append(variante.get_data())
                else:
                    hashp = ''
                    for row in self.database.get_variation(variante):
                        hashp = str(row['hash'])
                        logging.debug("trovato: "+hashp)
                    if str(variante.md5hash()) not in hashp:
                        logging.info("Hash database: " + hashp + " Hash variante: " + variante.md5hash())
                        update.append(variante)
                        data["update"].append(variante.get_data())
                    else:
                        logging.debug("Gia aggiornato: " + str(variante))
            try:
                if create or update:
                    temp = self.wcapi.post("products/" + str(product_id) + "/variations/batch", data)
                    logging.info(temp.json())
                    if create:
                        for created, response in zip(create, temp.json()["create"]):
                            created.wcid = response['id']
                    if temp.status_code == 200 or temp.status_code == 201:
                        self.database.add_variations(create)
                        self.database.update_variations(update)
            except Exception as e:
                logging.warning(e)

    def update_product(self, product):
        self.batch_update_products([product])

    def update_variation(self, variante):
        id_padre = self.get_id_by_sku(variante.codice_padre)
        id_variante = self.get_id(variante)
        try:
            temp = self.wcapi.put("products/" + id_padre + "/variations/" + id_variante, variante.get_data())
            if temp.status_code == 200 or temp.status_code == 201:
                self.database.update_variation(variante)
        except Exception as e:
            logging.warning(e)
            return None

    def get_id(self, element, force_local=False):
        found = None
        try:
            for result in self.database.cerca_codice(element.codice):
                return result['wcid']
            if found is None and not force_local:
                try:
                    found = self.wcapi.get("products", params={'sku': element.sku})
                    if found.status_code == 200 or found.status_code == 201:
                        return found.json()[0]['id']
                    else:
                        return None
                except AttributeError:
                    found = self.wcapi.get("products/categories",
                                           params={'slug': element.slug})
                    if found.status_code == 200 or found.status_code == 201:
                        return found.json()[0]['id']
                    else:
                        return None
            else:
                return found
        except IndexError:
            return None

    def batch_disable_products(self, products, batch_max_size=100):
        for i in range(0, len(products), batch_max_size):
            data = {
                "update": []
            }
            for product in itertools.islice(products, i, i + batch_max_size):
                if product.wcid is None:
                    product.wcid = self.get_id(product)
                product_data = {
                    'id': product.wcid,
                    'status': 'private'
                }
                data["update"].append(product_data)
            try:
                self.wcapi.post("products/batch", data)
            except Exception as e:
                logging.warning(e)

    def add_category(self, category):
        temp = self.wcapi.post("products/categories", category.get_data())
        if temp.status_code == 200 or temp.status_code == 201:
            category.wcid = temp.json()['id']
            category.wcpid = temp.json()['parent']
            self.database.add_category(category)
        return temp

    def update_category(self, category):
        temp = self.wcapi.put("products/categories/" + str(self.get_id(category)), category.get_data())
        self.database.update_category(category)
        return temp

    def batch_update_categories(self, categories, batch_max_size=100):
        for i in range(0, len(categories), batch_max_size):
            create = []
            update = []
            data = {
                "create": [],
                "update": []
            }
            for category in itertools.islice(categories, i, i + batch_max_size):
                if category.wcid is None:
                    temp_wcid = self.get_id(category)
                    logging.debug("found:" + category.nome)
                    if temp_wcid is not None:
                        category.wcid = temp_wcid
                if category.wcpid is None:
                    for res in self.database.cerca_codice(category.codice_padre):
                        category.wcpid = res['wcid']
                        logging.debug("fathet has id: " + str(category.wcpid))
                if category.wcid is None:
                    create.append(category)
                    data["create"].append(category.get_data())
                else:
                    update.append(category)
                    data["update"].append(category.get_data())
            try:
                logging.debug("adding " +str(len(create)))
                temp = self.wcapi.post("products/categories/batch", data)
                if create:
                    for created, response in zip(create, temp.json()["create"]):
                        created.wcid = response['id']
                if temp.status_code == 200 or temp.status_code == 201:
                    self.database.update_categories(update)
                    self.database.add_categories(create)
            except Exception as e:
                logging.warning(e)

    def batch_add_categories(self, categories, batch_max_size=100):
        for i in range(0, len(categories), batch_max_size):
            data = {
                "create": []
            }
            for category in itertools.islice(categories, i, i + batch_max_size):
                data["create"].append(category.get_data())
            try:
                temp = self.wcapi.post("products/categories/batch", data)
                if temp.status_code == 200 or temp.status_code == 201:
                    self.database.add_categories(itertools.islice(categories, i, i + batch_max_size))
            except Exception as e:
                logging.warning(e)

    def get_id_by_sku(self, sku):
        found = None
        try:
            for result in self.database.cerca_codice(sku):
                found = result['wcid']
            if found is None:
                return self.wcapi.get("products", params={'sku': sku}).json()[0]['id']
        except IndexError:
            return None

    def get_id_by_slug(self, slug):
        found = None
        try:
            for result in self.database.cerca_codice(slug):
                found = result['wcid']
            if found is None:
                temp = self.wcapi.get("products", params={'slug': slug}).json()
                return temp[0]['id']
        except KeyError:
            return None
