from flask import url_for
from ontospy.core.utils import uri2niceString
from rdflib import RDFS, Literal


class RDFClass:
    def __init__(self, uriref, graph):
        self.uriref = uriref
        self.namespaces = graph.namespaces
        self.graph = graph

    def title(self):
        name = uri2niceString(self.uriref, self.namespaces())
        uri, name = name.split(':')
        return name

    def label(self):
        title = None
        for title_triplet in self.graph.triples((self.uriref, RDFS.label, None)):
            if type(title_triplet[2]) != Literal or title_triplet[2].language != 'en':
                continue
            title = title_triplet[2]
        if not title:
            title = str(self)
        return title

    def get_absolute_url(self):
        name = uri2niceString(self.uriref, self.namespaces())
        uri, name = name.split(':')
        if uri != 'pot':
            return '#'
        return url_for('rdftools.get_class', class_name=name)

    def get_properties(self):
        attributes = []
        for attr in self.graph.triples((None, RDFS.domain, self.uriref)):
            attributes.append(RDFProperty(attr[0], self.graph))
        attributes = sorted(attributes, key=lambda x: str(x))
        return attributes

    def get_parents(self):
        parents = []
        try:
            parent = list(self.graph.triples((self.uriref, RDFS.subClassOf, None)))[0]
        except IndexError:
            return []
        while parent:
            parents.append(RDFClass(parent[2], self.graph))
            if parent[2] != self.uriref:
                try:
                    parent = list(self.graph.triples((parent[2], RDFS.subClassOf, None)))[0]
                except IndexError:
                    break
        parents.reverse()
        return parents

    def __str__(self):
        return uri2niceString(self.uriref, self.namespaces())


class RDFProperty:
    def __init__(self, uriref, graph):
        self.uriref = uriref
        self.namespaces = graph.namespaces
        self.graph = graph

    def label(self):
        title = None
        for title_triplet in self.graph.triples((self.uriref, RDFS.label, None)):
            if type(title_triplet[2]) != Literal or title_triplet[2].language != 'en':
                continue
            title = title_triplet[2]
        if not title:
            title = str(self)
        return title

    def get_supported_range(self):
        supported = []
        for item in self.graph.triples((self.uriref, RDFS.range, None)):
            supported.append(RDFClass(item[2], self.graph))
        return supported

    def get_absolute_url(self):
        name = uri2niceString(self.uriref, self.namespaces())
        uri, name = name.split(':')
        if uri != 'pot':
            return '#'
        return url_for('rdftools.get_property', property_name=name)

    def get_domains(self):
        domains = []
        for domain in self.graph.triples((self.uriref, RDFS.domain, None)):
            domains.append(RDFClass(domain[2], self.graph))
        return domains

    def __str__(self):
        return uri2niceString(self.uriref, self.namespaces())