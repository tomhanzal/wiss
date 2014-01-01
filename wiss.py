import os, re
from flask import Flask, render_template, request, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON


app = Flask(__name__)


def get_sparql_query(what, q):
    if what == 'search':
        sparql_query = """
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX ore: <http://www.openarchives.org/ore/terms/>
            PREFIX edm: <http://www.europeana.eu/schemas/edm/>

            SELECT ?title ?content_type ?content_provider ?link ?image ?object (GROUP_CONCAT(?desc ; SEPARATOR = " ") AS ?description) (GROUP_CONCAT(?au ; SEPARATOR = ";") AS ?author)
            WHERE {
              ?proxy dc:subject "%s";
                dc:title ?title ;
                dc:creator ?au ;
                ore:proxyIn [edm:isShownAt ?link; edm:object ?image; edm:dataProvider ?content_provider] ;
                ore:proxyFor ?object ;
                edm:type ?content_type ;
                dc:description ?desc .
            }
            GROUP BY ?object ?title ?content_type ?content_provider ?link ?image ?author
            LIMIT 100
        """ % q

    elif what == 'search_author':
        sparql_query = """
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX ore: <http://www.openarchives.org/ore/terms/>
            PREFIX edm: <http://www.europeana.eu/schemas/edm/>

            SELECT ?title ?author ?content_type ?content_provider ?link ?image ?object (GROUP_CONCAT(?desc ; SEPARATOR = " ") AS ?description)
            WHERE {
              ?proxy dc:creator "%s", ?author ;
                dc:title ?title ;
                dc:description ?desc ;
                ore:proxyIn [edm:isShownAt ?link; edm:object ?image; edm:dataProvider ?content_provider] ;
                ore:proxyFor ?object ;
                edm:type ?content_type .
            }
            GROUP BY ?object ?title ?content_type ?content_provider ?link ?image ?author
            LIMIT 40
        """ % q

    elif what == 'search_uri':
        sparql_query = """
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX ore: <http://www.openarchives.org/ore/terms/>
            PREFIX edm: <http://www.europeana.eu/schemas/edm/>

            SELECT ?title ?author ?description ?content_type ?content_provider ?link ?image ?object
            WHERE {
              ?proxy1 edm:hasMet <%s> ;
                ore:proxyFor ?object .
              ?proxy dc:title ?title ;
                dc:creator ?author ;
                dc:description ?description ;
                ore:proxyIn [edm:isShownAt ?link; edm:object ?image; edm:dataProvider ?content_provider] ;
                ore:proxyFor ?object ;
                edm:type ?content_type .
            }
            LIMIT 100
        """ % q

    elif what == 'get_author_info':
        sparql_query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX yago: <http://dbpedia.org/class/yago/>

            SELECT ?name ?abstract ?image ?link
            WHERE {
              ?person foaf:name "%s"@en ;
                a yago:Artist109812338 ;
                dbo:abstract ?abstract ;
                foaf:name ?name ;
                foaf:isPrimaryTopicOf ?link .
              optional {?person foaf:depiction ?image . }
              filter(lang(?abstract) = "en")
            }
            LIMIT 1
        """ % q

    elif what == 'get_subjects':
        sparql_query = """
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX ore: <http://www.openarchives.org/ore/terms/>
            PREFIX edm: <http://www.europeana.eu/schemas/edm/>

            SELECT ?subject
            WHERE {
              {
              ?proxy ore:proxyFor %s ;
                dc:subject ?subject .
              }
              UNION {
              ?proxy ore:proxyFor %s ;
                edm:hasMet ?subject .
              }
            }
        """ % (q, q)

    elif what == 'get_gemet_label':
        sparql_query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

            SELECT ?label
            WHERE {
              <%s> skos:prefLabel ?label .
              filter(lang(?label) = "en")
            }
        """ % q

    return sparql_query
        


def convert_name(name):
    output = re.sub('\s\(\w*\)', '', name)
    if ',' in output:
        output = output.split(', ')
        output = '%s %s' % (output[1], output[0])
    return output


@app.route('/')
def homepage():
    return render_template('homepage.html')


@app.route('/search')
def search():
    query = request.args.get('q', '', type=str)

    sparql = SPARQLWrapper("http://europeana.ontotext.com/sparql")
    sparql.setQuery(get_sparql_query('search', query))

    # If searching by URI...
    if query[0:7] == "http://":
        sparql.setQuery(get_sparql_query('search_uri', query))

    sparql.setReturnFormat(JSON)

    objects = list()
    idnum = 0

    try:
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            desc = result["description"]["value"]
            if len(desc) > 500:
                desc = desc[0:500] + " [...]"
            authors = result["author"]["value"].split(';')

            objects.append({
                "title": result["title"]["value"],
                "author": authors,
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
    except KeyError:
        return render_template('not_found.html', query=query)


@app.route('/search/author')
def search_author():
    query = request.args.get('q', '', type=str)

    sparql = SPARQLWrapper("http://europeana.ontotext.com/sparql")
    sparql.setQuery(get_sparql_query('search_author', query))

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
            "author": [result["author"]["value"]],
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
    author = convert_name(author)

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(get_sparql_query('get_author_info', author))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    result = results["results"]["bindings"][0]

    abstract = result["abstract"]["value"]
    if len(abstract) > 1000:
        abstract = abstract[0:1000] + " [...]"

    author_info = dict()
    author_info["abstract"] = abstract
    author_info["image"] = result["image"]["value"]
    author_info["link"] = result["link"]["value"]
    author_info["name"] = result["name"]["value"]

    return jsonify(author_info)


@app.route('/s')
def list_subjects():
    obj = request.args.get('obj', '', type=str)
    obj = "<%s>" % obj

    sparql = SPARQLWrapper("http://europeana.ontotext.com/sparql")
    sparql.setQuery(get_sparql_query('get_subjects', obj))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    subjects = list()

    for result in results["results"]["bindings"]:
        subject = result["subject"]["value"]
        label = subject

        # Label GEMET thesaurus URIs
        if subject[0:42] == "http://www.eionet.europa.eu/gemet/concept/":

            sparql = SPARQLWrapper("http://semantic.eea.europa.eu/sparql")
            sparql.setQuery(get_sparql_query('get_gemet_label', subject))
            sparql.setReturnFormat(JSON)
            thes_result = sparql.query().convert()

            label = "%s (%s)" % (thes_result["results"]["bindings"][0]["label"]["value"], subject)


        subjects.append({"subject": subject, "label": label})

    return jsonify(dict({"subjects": subjects}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
