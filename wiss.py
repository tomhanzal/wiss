import os
from flask import Flask, render_template, request, jsonify
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

        select ?title ?author ?description ?content_type ?content_provider ?link ?image ?object
        where {
          ?proxy dc:subject "%s";
            dc:title ?title ;
            dc:creator ?author ;
            dc:description ?description ;
            ore:proxyIn [edm:isShownAt ?link; edm:object ?image; edm:dataProvider ?content_provider] ;
            ore:proxyFor ?object ;
            edm:type ?content_type .
        }
        limit 40
    """ % query)

    # If searching by GEMET thesaurus URI...
    if query[0:7] == "http://":
        sparql.setQuery("""
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX ore: <http://www.openarchives.org/ore/terms/>
            PREFIX edm: <http://www.europeana.eu/schemas/edm/>

            select ?title ?author ?description ?content_type ?content_provider ?link ?image ?object
            where {
              ?proxy1 edm:hasMet <%s> ;
                ore:proxyFor ?object .
              ?proxy dc:title ?title ;
                dc:creator ?author ;
                dc:description ?description ;
                ore:proxyIn [edm:isShownAt ?link; edm:object ?image; edm:dataProvider ?content_provider] ;
                ore:proxyFor ?object ;
                edm:type ?content_type .
            }
            limit 40
        """ % query)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    objects = list()
    idnum = 0

    for result in results["results"]["bindings"]:
        desc = result["description"]["value"]
        if len(desc) > 500:
            desc = desc[0:500] + " [...]"

        objects.append({
            "title": result["title"]["value"],
            "author": result["author"]["value"],
            "description": desc,
            "content_type": result["content_type"]["value"],
            "content_provider": result["content_provider"]["value"],
            "content_link": result["link"]["value"],
            "picture": result["image"]["value"],
            "id": idnum,
            "obj": result["object"]["value"]
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
        PREFIX ore: <http://www.openarchives.org/ore/terms/>
        PREFIX edm: <http://www.europeana.eu/schemas/edm/>

        select ?subject
        where {
          {
          ?proxy ore:proxyFor %s ;
            dc:subject ?subject .
          }
          union {
          ?proxy ore:proxyFor %s ;
            edm:hasMet ?subject .
          }
        }
    """ % (obj, obj))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    subjects = list()

    for result in results["results"]["bindings"]:
        subject = result["subject"]["value"]
        label = subject

        # Label GEMET thesaurus URIs
        if subject[0:42] == "http://www.eionet.europa.eu/gemet/concept/":

            sparql = SPARQLWrapper("http://semantic.eea.europa.eu/sparql")
            sparql.setQuery("""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT ?label
                WHERE {
                  <%s> skos:prefLabel ?label .
                  filter(lang(?label) = "en")
                }
            """ % subject)
            sparql.setReturnFormat(JSON)
            thes_result = sparql.query().convert()

            label = "%s (%s)" % (thes_result["results"]["bindings"][0]["label"]["value"], subject)


        subjects.append({"subject": subject, "label": label})

    return jsonify(dict({"subjects": subjects}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
