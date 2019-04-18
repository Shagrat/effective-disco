from flask import flash
from rdflib import RDF, RDFS, Graph, Namespace, OWL, Literal
from rdflib import URIRef
from effective_disco.rdftools.const import POT_BASE
from effective_disco.rdftools.models import RDFClass, RDFProperty


def build_uriref(string, graph):
    try:
        prefix, name = string.split(':')
    except ValueError:
        return None
    for x, i in graph.namespaces():
        if x == prefix:
            uriref = i+name
            break
    else:
        return None
    return uriref


def build_class_info(class_prefix, class_name, graph):
    for x, i in graph.namespaces():
        if x == class_prefix:
            uriref = i+class_name
            break
    else:
        return None
    return RDFClass(uriref, graph)




def build_property_info(attribute_prefix, attribute_name, graph):
    for x, i in graph.namespaces():
        if x == attribute_prefix:
            uriref = i+attribute_name
            break
    else:
        return None
    return RDFProperty(uriref, graph)


def build_classes(graph):
    triples = []
    for triplet in graph.triples((None, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
                                  URIRef('{}ontologies/pot.jsonld#Class'.format(POT_BASE)))):
        triples.append(RDFClass(triplet[0], graph))
    triples = sorted(triples, key= lambda x: str(x))
    return {
        'count': len(triples),
        'tree': triples
    }


def build_properties(graph, class_to_exclude=None):
    triples = []
    for triplet in graph.triples((None, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
                                   RDF.Property)):
        triples.append(RDFProperty(triplet[0], graph))
    triples = sorted(triples, key=lambda x: str(x))
    if class_to_exclude:
        triples = set(triples).difference(set(class_to_exclude.get_properties()))
    return {
        'count': len(triples),
        'tree': triples
    }


def add_property_to_class(property, rdf_class, graph):
    try:
        prefix, name = property.split(':')
    except:
        flash('Wrong property ID')
        return graph
    for x, i in graph.namespaces():
        if x == prefix:
            uriref = i+name
            break
    else:
        return graph
    graph.add((uriref, RDFS.domain, rdf_class.uriref))
    return graph


def remove_property_from_class(property, rdf_class, graph):
    try:
        prefix, name = property.split(':')
    except:
        flash('Wrong property ID')
        return graph
    for x, i in graph.namespaces():
        if x == prefix:
            uriref = i+name
            break
    else:
        return graph
    graph.remove((uriref, RDFS.domain, rdf_class.uriref))
    return graph


def add_property_to_graph(property_name, property_label, graph):
    g = Graph()
    ns = Namespace('https://standards.oftrust.net/ontologies/pot.jsonld#')
    SW = Namespace('http://www.w3.org/2003/06/sw-vocab-status/ns#')
    g.add((ns.term(property_name), RDF.type, RDF.Property))
    g.add((ns.term(property_name), OWL.versionInfo, Literal('DRAFT')))
    g.add((ns.term(property_name), SW.term_status, Literal('unstable')))
    g.add((ns.term(property_name), RDFS.label, Literal(property_label, lang='en')))
    graph = graph + g

    return graph, RDFProperty(ns.term(property_name), graph)


def remove_property_from_graph(rdf_property, graph):
    graph.remove((rdf_property.uriref, None, None))
    graph.remove((None, None, rdf_property.uriref))
    return graph


def remove_class_from_graph(rdf_class, graph):
    graph.remove((rdf_class.uriref, None, None))
    graph.remove((None, None, rdf_class.uriref))
    return graph


def add_class_to_graph(class_name, class_label, parent_class, graph):
    g = Graph()
    ns = Namespace('https://standards.oftrust.net/ontologies/pot.jsonld#')
    SW = Namespace('http://www.w3.org/2003/06/sw-vocab-status/ns#')
    g.add((ns.term(class_name), RDF.type, ns.Class))
    if parent_class:
        g.add((ns.term(class_name), RDFS.subClassOf, URIRef(parent_class)))
    g.add((ns.term(class_name), OWL.versionInfo, Literal('DRAFT')))
    g.add((ns.term(class_name), SW.term_status, Literal('unstable')))
    g.add((ns.term(class_name), RDFS.label, Literal(class_label, lang='en')))
    graph = graph + g
    return graph, RDFClass(ns.term(class_name), graph)
