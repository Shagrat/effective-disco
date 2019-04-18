# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask, session

from effective_disco import rdftools
from effective_disco.settings import ProdConfig
from effective_disco.rdftools.views import blueprint
from flask_session import Session


def create_app(config_object=ProdConfig):
    """An application factory, as explained here:
    http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_object)
    Session(app)
    register_blueprints(app)
    return app


def register_blueprints(app):
    app.register_blueprint(rdftools.views.blueprint)
