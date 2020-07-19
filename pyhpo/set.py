class HPOSet(list):
    def child_nodes(self):
        """
        Return a new HPOSet tha contains only
        the most specific HPO term for each subtree

        It basically will return only HPO terms
        that do not have descendant HPO terms
        present in the set

        Returns
        -------
        HPOSet
            HPOSet instance that contains only the most specific
            child nodes of the current HPOSet
        """
        counter = {term.id: 0 for term in self}
        for child, parent in self.combinations():
            if child.child_of(parent):
                counter[parent.id] += 1
        return HPOSet([
            term for term in self if counter[term.id] == 0
        ])

    def remove_modifier(self):
        """
        Removes all modifier terms. By default, this includes

        * ``Mode of inheritance: 'HP:0000005'``
        * ``Clinical modifier: 'HP:0012823'``
        * ``Frequency: 'HP:0040279'``
        * ``Clinical course: 'HP:0031797'``
        * ``Blood group: 'HP:0032223'``
        * ``Past medical history: 'HP:0032443'``


        Returns
        -------
        HPOSet
            HPOSet instance that contains only
            ``Phenotypic abnormality`` HPO terms

        """

        # Parent modifier terms
        modifier = (5, 12823, 40279, 31797, 32223, 32443)

        counter = {term.id: 0 for term in self}
        for term in self:
            for mod in modifier:
                if mod in [int(parent) for parent in term.all_parents]:
                    counter[term.id] += 1
        return HPOSet([
            term for term in self if counter[term.id] == 0
        ])

    def all_genes(self):
        """
        Calculates the union of the genes
        attached to the HPO Terms in this set

        Returns
        -------
        set of :class:`annotations.Gene`
            Set of all genes associated with the HPOTerms in the set
        """
        genes = set()
        for term in self:
            genes.update(term.genes)
        return genes

    def information_content(self, kind=None):
        """
        Gives back basic information content stats about the
        HPOTerms within the set

        Parameters
        ----------
        kind: str, default: ``omim``
            Which kind of information content should be calculated.
            Options are ['omim', 'gene']


        Returns
        -------
        dict
            Dict with the following items

            * **mean** - float - Mean information content
            * **max** - float - Maximum information content value
            * **total** - float - Sum of all information content values
            * **all** - list of float -
              List with all information content values
        """
        if kind is None:
            kind = 'omim'

        res = {
            'mean': None,
            'total': 0,
            'max': 0,
            'all': [term.information_content[kind] for term in self]
        }
        res['total'] = sum(res['all'])
        res['max'] = max(res['all'])
        res['mean'] = res['total']/len(self)
        return res

    def variance(self):
        """
        Calculates the distances between all its term-pairs. It also provides
        basic calculations for variances among the pairs.

        Returns
        -------
        tuple of (int, int, int, list of int)
            Tuple with the variance metrices

            * **int** Average distance between pairs
            * **int** Smallest distance between pairs
            * **int** Largest distance between pairs
            * **list of int** List of all distances between pairs
        """

        distances = []
        for term_a, term_b in self.combinations_one_way():
            distances.append(term_a.path_to_other(term_b)[0])

        if len(distances):
            return (
                sum(distances)/len(distances),
                min(distances),
                max(distances),
                distances
            )
        else:
            return (0, 0, 0, [])

    def combinations(self):
        """
        Helper generator function that returns all possible two-pair
        combination between all its terms

        This function is direction dependent. That means that every
        pair will appear twice. Once for each direction

        .. seealso:: :func:`pyhpo.set.HPOSet.combinations_one_way`

        Yields
        ------
        Tuple of :class:`term.HPOTerm`
            Tuple containing the follow items

            * **HPOTerm** instance 1 of the pair
            * **HPOTerm** instance 2 of the pair

        Examples
        --------
            ::

                ci = HPOSet([term1, term2, term3])
                ci.combinations()

                # Output:
                [
                    (term1, term2),
                    (term1, term3),
                    (term2, term1),
                    (term2, term3),
                    (term3, term1),
                    (term3, term2)
                ]

        """
        for term_a in self:
            for term_b in self:
                if term_a == term_b:
                    continue
                yield (term_a, term_b)

    def combinations_one_way(self):
        """
        Helper generator function that returns all possible two-pair
        combination between all its terms

        This methow will report each pair only once

        .. seealso:: :func:`pyhpo.set.HPOSet.combinations`

        Yields
        ------
        Tuple of :class:`term.HPOTerm`
            Tuple containing the follow items

            * **HPOTerm** instance 1 of the pair
            * **HPOTerm** instance 2 of the pair

        Example
        -------
            ::

                ci = HPOSet([term1, term2, term3])
                ci.combinations()

                # Output:
                [
                    (term1, term2),
                    (term1, term3),
                    (term2, term3)
                ]

        """
        for i, term_a in enumerate(self):
            for term_b in self[i+1:]:
                yield (term_a, term_b)

    def similarity(self, other, kind='omim'):
        """
        Calculates the similarity to another HPOSet
        According to Robinson et al, American Journal of Human Genetics, (2008)
        and Pesquita et al, BMC Bioinformatics, (2008)

        Parameters
        ----------
        other: HPOSet
            Another HPOSet to measure the similarity to

        kind: str, default ``omim``
            Which kind of information content should be calculated.
            Options are ['omim', 'gene']

        Returns
        -------
        float
            The similarity score to the other HPOSet

        """
        score1 = HPOSet._sim_score(self, other, kind)
        score2 = HPOSet._sim_score(other, self, kind)
        return (score1 + score2)/2

    @staticmethod
    def _sim_score(set1, set2, kind):
        """
        Calculates one-way similarity from one HPOSet to another HPOSet

        .. warning::

           This method should not be used by itself.
           Use :func:`pyhpo.set.HPOSet.similarity` instead.

        Parameters
        ----------
        set1: HPOSet
            One HPOSet to measure the similarity from
        set2: HPOSet
            Another HPOSet to measure the similarity to

        kind: str
            Which kind of information content should be calculated.
            Options are ['omim', 'gene']

        Returns
        -------
        float
            The one-way similarity from one to the other HPOSet

        """

        if not len(set1) or not len(set2):
            return 0

        scores = []
        for set1_term in set1:
            scores.append(0)
            for set2_term in set2:
                score = set1_term.similarity_score(set2_term, kind)
                if score > scores[-1]:
                    scores[-1] = score
        return sum(scores)/len(scores)

    @staticmethod
    def from_ontology(ontology, queries):
        """
        Builds an HPO set by specifying a list of queries to run on an
        :class:`pyhpo.ontology.Ontology` object

        Parameters
        ----------
        ontology: :class:`pyhpo.ontology.Ontology`
            The HPO Ontology that will be used to get HPOTerms

        queries: list of (string or int)
            The queries to be run the identify the HPOTerm from the ontology

        Returns
        -------
        :class:`pyhpo.set.HPOSet`
            A new HPOset

        Examples
        --------
            ::

                ci = HPOSet(ontology, [
                    'Scoliosis',
                    'HP:0001234',
                    12
                ])

        """
        return HPOSet([
            ontology.get_hpo_object(query) for query in queries
        ])

    @staticmethod
    def from_serialized(ontology, pickle):
        """
        Re-Builds an HPO set from a serialized HPOSet object

        Parameters
        ----------
        ontology: :class:`pyhpo.ontology.Ontology`
            The HPO Ontology that will be used to get HPOTerms

        pickle: str
            The serialized HPOSet object

        Returns
        -------
        :class:`pyhpo.set.HPOSet`
            A new HPOset

        Examples
        --------
            ::

                ci = HPOSet(ontology, '12+24+66628')

        """
        return HPOSet([
            ontology.get_hpo_object(int(query)) for query in pickle.split('+')
        ])

    def serialize(self):
        """
        Creates a string serialization that can be used to
        rebuild the same HPOSet via `pyhpo.set.HPOSet.from_serialized`

        Returns
        -------
        str
            A string representation of the HPOSet

        """
        ids = [str(x) for x in sorted([int(x) for x in self])]
        return '+'.join(ids)

    def toJSON(self, verbose=False):
        """
        Creates a JSON-like object of the HPOSet

        Parameters
        ----------
        verbose: bool, default ``False``
            Include extra properties of the HPOTerm

        Returns
        -------
        list of dict
            a list of HPOTerm dict objects

        """
        return [t.toJSON(verbose) for t in self]

    def __str__(self):
        return 'HPOSet: {}'.format(
            ', '.join([x.name for x in self])
        )

    def __repr__(self):
        return 'HPOSet(ontology, {})'.format(
            ', '.join([x.id for x in self])
        )
