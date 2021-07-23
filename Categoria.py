import re


def slugify(text):
    text = text.lower()
    return re.sub(r'[\W_]+', '-', text)


class Categoria:

    def __init__(self, codice, codice_padre, descrizione, nome, img_src=None):
        self.descrizione = descrizione
        self.nome = nome
        self.codice = str(codice)
        self.codice_padre = str(codice_padre)
        self.woocommerce_id = None
        self.woocommerce_parent_id = None
        self.img_src = img_src

    def get_data(self):
        data = {
            "name": self.nome,
            "description": self.descrizione,
            "slug": str(self.codice) + "-" + slugify(self.nome)
        }
        if self.img_src is not None:
            data['image'] = {"src": self.img_src}
        if self.wcpid is not None:
            data['parent'] = self.wcpid
        if self.wcid is not None:
            data['id'] = self.wcid
        return data

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

    @property
    def slug(self):
        return str(self.codice) + "-" + slugify(self.nome)

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )
