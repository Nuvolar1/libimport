import hashlib


class Prodotto:

    def __init__(self, codice, codice_categoria, nome, descrizione, varianti=None, img_src=None, instock=True):
        if varianti is None:
            varianti = []
        self.codice = str(codice)
        self.codice_categoria = str(codice_categoria)
        self.nome = nome
        self.descrizione = descrizione
        self.varianti = list(varianti)
        self.woocommerce_id = None
        self.woocommerce_cid = None
        self.img_src = img_src
        self.instock = instock

    def __codici_varianti(self):
        codici = []
        for variante in self.varianti:
            codici.append(variante.sku)
        return codici

    def get_data(self):
        data = {
            "name": self.nome,
            "type": "variable",
            "description": self.descrizione,
            "sku": self.codice,
            "attributes": [
                {
                    "position": 0,
                    "visible": True,
                    "variation": True,
                    "name": "Codice",
                    "options": self.__codici_varianti()
                }
            ]
        }
        if not self.instock:
            data['stock_status'] = 'outofstock'
        else:
            data['stock_status'] = 'instock'
        if self.wccid is not None:
            data['categories'] = [{"id": self.wccid}]
        if self.img_src is not None:
            data['image'] = {"src": self.img_src}
        return data

    def get_variations(self):
        return self.varianti

    def append_variations(self, variations):
        for variation in variations:
            variation.codice_padre = self.codice
            self.varianti.append(variation)

    def md5hash(self):
        hasher = hashlib.md5()
        megastring = ''
        for variante in self.varianti:
            megastring += str(variante)
        megastring += str(self.get_data())
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
    def wccid(self):
        return self.woocommerce_cid

    @wccid.setter
    def wccid(self, value):
        self.woocommerce_cid = value
