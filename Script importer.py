from __future__ import division
import csv
import datetime
import logging
from woocommerce import API
import Importer
import Prodotto
import Variante
import Categoria
from multiprocessing import Pool
import asyncio

logging.basicConfig(filename='../../.config/JetBrains/PyCharmCE2021.1/scratches/example.log', level=logging.INFO, format='%(asctime)s:'
                                                                       '%(levelname)s:%(message)s')


def dialect_sniffer(file_path):
    with open(file_path) as file:
        dialect = csv.Sniffer().sniff(file.read(1024))
    return dialect


def work_log(work_data):
    process_worker = Importer.Importer(wcapi, 'localhost', 'script', 'scriptpass', database='importer')
    process_worker.batch_update_products([work_data], force_local=False, force_add=False)
    process_worker.close_database()
    del process_worker


wcapi = API(
    url='http://syc-local/',
    consumer_key='ck_d9907a60e8b68092345476ed3c669dcba60e22f2',
    consumer_secret='cs_bebc262439c4fb623e6d635bcb873363c28aa38c',
    timeout=5000,
    wp_api=True,
    version='wc/v3',
    query_string_auth=True
)

#worker = Importer.Importer(wcapi, 'localhost', 'script', 'scriptpass', database='importer')

#worker.initialize_database()

categories = []
with open("/categorie.csv", 'r') as f:
    csv_reader = csv.DictReader(f, dialect=dialect_sniffer("/categorie.csv"))
    for row in csv_reader:
        categories.append(
            Categoria.Categoria(str(row['Codice Categoria/Nodo']), str(row['Codice Categoria/Nodo Padre']),
                                row['Descrizione Categoria/Nodo Italiana'], row['Nome Categoria/Nodo Italiana']))

#worker.batch_update_categories(categories, batch_max_size=10)

products = {}

with open("/prodotti.csv", 'r') as f:
    csv_reader = csv.DictReader(f, dialect=dialect_sniffer("/categorie.csv"))
    for row in csv_reader:
        products[row['Codice Categoria/Nodo']] = Prodotto.Prodotto(row['Codice Categoria/Nodo'],
                                                                   row['Codice Categoria/Nodo Padre'],
                                                                   row['Nome Categoria/Nodo Italiana'],
                                                                   row['Descrizione Categoria/Nodo Italiana'])
print(products)

with open("/varianti.csv", 'r') as f:
    csv_reader = csv.DictReader(f, dialect=dialect_sniffer("/categorie.csv"))
    for row in csv_reader:
        try:
            products[row['Codice Categoria']].append_variations([Variante.Variante(row['Codice Prodotto'],
                                                                                   row['Codice Categoria'], row[
                                                                                       'Descrizione Prodotto Breve Italiana'],
                                                                                   row['Listino Base'], img_src='https://pbs.twimg.com/profile_images/949787136030539782/LnRrYf6e.jpg')])
        except KeyError as e:
            print("categoria" + str(e) + "non trovata")
'''
for product in products.values():
    product.instock = False
    for variante in product.get_variations():
        if variante.instock:
            product.instock = True
            break
'''
sauce = list(products.values())[:10]
num_tasks = len(sauce)

p = Pool(4)

start_time = datetime.datetime.now()

for i, _ in enumerate(p.imap_unordered(work_log, sauce), 1):
    logging.debug('\rPercentuale prodotti aggiunti: {0:%}'.format(i / num_tasks))
    print('percentuale completata: {0:%}'.format(i / num_tasks))
    estimate = ((datetime.datetime.now() - start_time) / i) * (num_tasks - i)
    print("tempo rimasto stimato: " + str(estimate))
    print("tempo trascorso: " + str(datetime.datetime.now() - start_time))
    time = datetime.datetime.now()

# worker.batch_update_products(sauce)

# worker.disable_products(sauce)
# worker.update_product(product, worker.get_id(product))
# worker.batch_update_variations(variation, worker.get_id(product))


# worker.add_category(Categoria.Categoria("46286", "4392849", "sus", "naus"))
