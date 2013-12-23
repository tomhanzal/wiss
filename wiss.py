import os
from flask import Flask
from flask import render_template
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('layout.html')

@app.route('/s', methods=['GET', 'POST'])
def search():
    q = request.form['q']

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?label
        WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    chos = dict()

    for result in results["results"]["bindings"]:
        chos.update(result["label"]["value"])

    return chos

    #return render_template('layout.html', chos=chos) 


if __name__ == '__main__':
    app.run()
