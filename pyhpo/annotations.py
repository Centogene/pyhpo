from pyhpo.term import HPOTerm

FILENAMES = {
    'HPO_GENE': 'ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes.txt',
    'HPO_PHENO': 'phenotype_annotation_hpoteam.tab',
    'HPO_NEGATIVE_PHENO': 'negative_phenotype_annotation.tab'
}


class Gene:
    def __init__(self, columns):
        self.id = int(columns[2])
        self.name = columns[3]

    @property
    def symbol(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, int):
            return self.id == other

        if isinstance(other, str):
            return self.id == other or self.name == other

        try:
            return self.id == other.id
        except AttributeError:
            return False

        return False

    def __hash__(self):
        return self.id

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Gene(["", "", {}, "{}"])'.format(
            self.id,
            self.name
        )


class Omim:
    def __init__(self, cols):
        self.id = int(cols[1])
        self.name = cols[2]

    def __eq__(self, other):
        if isinstance(other, int):
            return self.id == other

        if isinstance(other, str):
            return self.id == other or self.name == other

        try:
            return self.id == other.id
        except AttributeError:
            return False

        return False

    def __hash__(self):
        return self.id

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Omim(["", {}, "{}"])'.format(
            self.id,
            self.name
        )


class HPO_Gene(dict):
    def __init__(self, filename=None):
        if filename is None:
            filename = FILENAMES['HPO_GENE']
        self.load_from_file(filename)

    def load_from_file(self, filename):
        with open(filename) as fh:
            for line in fh:
                if line.startswith('#'):
                    continue
                cols = line.strip().split('\t')
                idx = HPOTerm.id_from_string(cols[0])
                if idx not in self:
                    self[idx] = set()
                gene = Gene(cols)
                if gene not in self[idx]:
                    self[idx].add(gene)


class HPO_Omim(dict):
    def __init__(self, filename=None):
        if filename is None:
            filename = FILENAMES['HPO_PHENO']
        self.load_from_file(filename)

    def load_from_file(self, filename):
        with open(filename) as fh:
            for line in fh:
                if not line.startswith('OMIM'):
                    continue
                cols = line.strip().split('\t')
                idx = HPOTerm.id_from_string(cols[4])
                if idx not in self:
                    self[idx] = set()
                omim = Omim(cols)
                if omim not in self[idx]:
                    self[idx].add(omim)


class HPO_negative_Omim(dict):
    def __init__(self, filename=None):
        if filename is None:
            filename = FILENAMES['HPO_NEGATIVE_PHENO']
        self.load_from_file(filename)

    def load_from_file(self, filename):
        with open(filename) as fh:
            for line in fh:
                if not line.startswith('OMIM'):
                    continue
                cols = line.strip().split('\t')
                if cols[3] != 'NOT':
                    continue
                idx = HPOTerm.id_from_string(cols[4])
                if idx not in self:
                    self[idx] = set()
                omim = Omim(cols)
                if omim not in self[idx]:
                    self[idx].add(omim)
