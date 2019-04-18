# -*- coding: utf-8 -*-
"""RDFTools views."""
import io
import re
from functools import wraps

from rdflib import ConjunctiveGraph
from flask import Blueprint, request, render_template, session, redirect, flash, url_for, send_file
import ontospy

from effective_disco.rdftools.utils import build_classes, build_properties, build_class_info, build_property_info, \
    add_property_to_class, remove_property_from_class, add_property_to_graph, remove_property_from_graph, \
    add_class_to_graph, remove_class_from_graph, build_uriref

blueprint = Blueprint('rdftools', __name__)


def get_graph_from_store():
    graph = ConjunctiveGraph().parse(data=session.get('stored_graph'))
    graph.namespace_manager.bind('pot', 'https://standards.oftrust.net/ontologies/pot.jsonld#')
    graph.namespace_manager.bind('dli', 'https://digitalliving.github.io/standards/ontologies/dli.jsonld#')
    return graph


def save_graph(graph):
    session['stored_graph'] = graph.serialize()


def graph_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        stored_graph = session.get('stored_graph', None)
        if not stored_graph:
            flash('You have to load graph first')
            return redirect(url_for('rdftools.get_meta'))
        return f(*args, **kwargs)
    return decorated_function


@blueprint.route('/meta', methods=('GET',))
def get_meta():
    stored_graph = session.get('stored_graph', None)
    if stored_graph:
        graph = get_graph_from_store()
        onto_data = ontospy.Ontospy(data=stored_graph, verbose=False)
        annotations = []
        for onto in onto_data.all_ontologies:
            annotations.extend(onto.annotations())
        return render_template('index.html', **{
            'stored_graph': graph,
            'namespaces': list(onto_data.namespaces),
            'annotations': annotations,
        })
    return render_template('index.html', **{
    })


@blueprint.route('/', methods=('GET',))
@graph_required
def get_entities():
    graph = get_graph_from_store()
    classes = build_classes(graph)
    properties = build_properties(graph)
    return render_template('entities.html', **{
        'classes': classes,
        'properties': properties,
    })


@blueprint.route('/classes/pot-<class_name>', methods=('GET', 'POST'))
@graph_required
def get_class(class_name):
    graph = get_graph_from_store()
    rdf_class = build_class_info('pot', class_name, graph)
    if request.method == 'POST':
        if request.form.get('add_property', None):
            graph = add_property_to_class(request.form.get('property_to_add', None), rdf_class, graph)
            save_graph(graph)
        elif request.form.get('property_to_remove', None):
            graph = remove_property_from_class(request.form.get('property_to_remove', None), rdf_class, graph)
            save_graph(graph)
        elif request.form.get('delete_class', None):
            graph = remove_class_from_graph(rdf_class, graph)
            save_graph(graph)
            return redirect(url_for('rdftools.get_entities'))
    return render_template('class.html', **{
        'rdf_class': rdf_class,
        'available_properties': build_properties(graph, class_to_exclude=rdf_class)
    })


@blueprint.route('/properties/pot-<property_name>', methods=('GET', 'POST'))
@graph_required
def get_property(property_name):
    graph = get_graph_from_store()
    rdf_property = build_property_info('pot', property_name, graph)
    if request.method == 'POST':
        if request.form.get('delete_property', None):
            graph = remove_property_from_graph(rdf_property, graph)
            save_graph(graph)
            return redirect(url_for('rdftools.get_entities'))
    return render_template('property.html', **{
        'rdf_property': rdf_property,
    })


@blueprint.route('/properties/add/', methods=('GET', 'POST'))
@graph_required
def create_property():
    if request.method == 'POST':
        property_name = request.form.get('property_name')
        property_label = request.form.get('property_label')
        graph = get_graph_from_store()
        if not bool(re.match("^[A-Za-z0-9]*$", property_name)):
            flash('Property ID must contain only letters and numbers')
            return render_template('add_property.html')
        graph, rdf_property = add_property_to_graph(property_name, property_label, graph)
        save_graph(graph)
        return redirect(rdf_property.get_absolute_url())
    return render_template('add_property.html', **{

    })


@blueprint.route('/class/add/', methods=('GET', 'POST'))
@graph_required
def create_class():
    graph = get_graph_from_store()
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        class_label = request.form.get('class_label')
        if not bool(re.match("^[A-Za-z0-9]*$", class_name)):
            flash('Property ID must contain only letters and numbers')
            return render_template('add_property.html')
        parent_class = build_uriref(request.form.get('parent_class', None), graph)
        if not parent_class:
            flash('Parent class can\'t be parsed in current graph')
            return render_template('add_class.html')
        graph, rdf_class = add_class_to_graph(class_name, class_label, parent_class, graph)
        save_graph(graph)
        return redirect(rdf_class.get_absolute_url())
    return render_template('add_class.html', **{
        'available_classes': build_classes(graph)
    })


@blueprint.route('/rdf/load-jsonld', methods=('POST',))
def load_rdf_schema():
    if request.method == 'POST':
        if 'rdffile' in request.files:
            rdffile = request.files.get('rdffile')
            if rdffile.filename == '':
                flash('No selected file')
            else:
                graph = ConjunctiveGraph().parse(data=rdffile.read(), format='json-ld')
                session['stored_graph'] = graph.serialize()
    return redirect('/meta')


@blueprint.route('/rdf/download-xml', methods=('GET',))
@graph_required
def download_graph_xml():
    graph = get_graph_from_store()
    result = graph.serialize()
    mem = io.BytesIO()
    mem.write(result)
    # seeking was necessary. Python 3.5.2, Flask 0.12.2
    mem.seek(0)
    return send_file(mem, mimetype="application/xml",
                     as_attachment=True,
                     attachment_filename='pot.xml',
                     cache_timeout=-1
                     )