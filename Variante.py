import hashlib

class Variante:

    def __init__(self, codice, codice_padre, nome, prezzo, img_src=None, instock=True):
        self.prezzo = prezzo
        self.codice = str(codice)
        self.codice_padre = codice_padre
        self.nome = nome
        self.woocommerce_id = None
        self.woocommerce_parent_id = None
        self.img_src = img_src
        self.instock = instock

    def get_data(self):
        data = {
            "regular_price": self.prezzo,
            "sku": self.codice,
            "description": self.nome,
            "attributes": [
                {
                    "name": "Codice",
                    "option": self.codice
                }
            ]
        }
        if not self.instock:
            data['stock_status'] = 'outofstock'
        else:
            data['stock_status'] = 'instock'
        if self.img_src is not None:
            data['image'] = {"src": self.img_src}
        if self.wcid is not None:
            data['id'] = self.wcid
        return data

    def md5hash(self):
        hasher = hashlib.md5()
        megastring = str(self.get_data())
        megastring = megastring.encode('utf-8')
        hasher.update(bytes(megastring))
        return hasher.hexdigest()


    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )

    @property
    def sku(self):
        return self.codice

    @sku.setter
    def sku(self, value):
        self.codice = value

    @property
    def wcid(self):
        return self.woocommerce_id

    @wcid.setter
    def wcid(self, value):
        self.woocommerce_id = value

    @property
    def wcpid(self):
        return self.woocommerce_parent_id

    @wcpid.setter
    def wcpid(self, value):
        self.woocommerce_parent_id = value
