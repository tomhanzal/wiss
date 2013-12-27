import os
from flask import Flask
from flask import render_template, request, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/search')
def search():
    query = request.args.get('q', '', type=str)

    sparql = SPARQLWrapper("http://europeana.ontotext.com/sparql")
    sparql.setQuery("""
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX ore: <http://www.openarchives.org/ore/terms/>
        PREFIX edm: <http://www.europeana.eu/schemas/edm/>

        select ?title ?author ?description ?content_type ?content_provider ?link ?image ?proxy
        where {
          ?proxy dc:subject "%s";
          dc:title ?title ;
          dc:creator ?author ;
          dc:description ?description ;
          ore:proxyIn [edm:isShownAt ?link; edm:object ?image; edm:dataProvider ?content_provider] ;
          edm:type ?content_type .
        }
        limit 40
    """ % query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    objects = list()
    idnum = 0

    for result in results["results"]["bindings"]:
        objects.append({
            "title": result["title"]["value"],
            "author": result["author"]["value"],
            "description": result["description"]["value"],
            "content_type": result["content_type"]["value"],
            "content_provider": result["content_provider"]["value"],
            "content_link": result["link"]["value"],
            "picture": result["image"]["value"],
            "id": idnum,
            "proxy": result["proxy"]["value"]
        })
        idnum = idnum + 1

    return render_template('search.html', chos=objects)

@app.route('/a')
def author_info():
    author = request.args.get('author', '', type=str)

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        select ?name ?abstract ?image ?link
        where {
          ?person foaf:name "%s"@en ;
            a dbo:Artist ;
            dbo:abstract ?abstract ;
            foaf:name ?name ;
            foaf:isPrimaryTopicOf ?link .
          optional {?person foaf:depiction ?image . }
          filter(lang(?abstract) = "en")
        }
        limit 1
    """ % author)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    result = results["results"]["bindings"][0]
    author_info = dict()
    author_info["abstract"] = result["abstract"]["value"]
    author_info["image"] = result["image"]["value"]
    author_info["link"] = result["link"]["value"]
    author_info["name"] = result["name"]["value"]

    return jsonify(author_info)

@app.route('/s')
def list_subjects():
    obj = request.args.get('obj', '', type=str)
    obj = "<%s>" % obj

    sparql = SPARQLWrapper("http://europeana.ontotext.com/sparql")
    sparql.setQuery("""
        PREFIX dc: <http://purl.org/dc/elements/1.1/>

        select ?subject
        where {
          %s dc:subject ?subject .
        }
    """ % obj)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    subjects = list()

    for result in results["results"]["bindings"]:
        subjects.append(result["subject"]["value"])

    return jsonify(dict({"subjects": subjects}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
