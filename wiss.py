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
    #if request.method == 'POST':
    #    q = request.form['q']

    sparql = SPARQLWrapper("http://europeana.ontotext.com/sparql")
    sparql.setQuery("""
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX ore: <http://www.openarchives.org/ore/terms/>
        PREFIX edm: <http://www.europeana.eu/schemas/edm/>

        select ?title ?author ?description ?content_type ?content_provider ?link ?image
        where {
          ?proxy dc:subject "love" ;
          dc:title ?title ;
          dc:creator ?author ;
          dc:description ?description ;
          ore:proxyIn [edm:isShownAt ?link; edm:object ?image; edm:dataProvider ?content_provider] ;
          edm:type ?content_type .
        }
        limit 12
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    objects = list()

    for result in results["results"]["bindings"]:
        objects.append({
            "title": result["title"]["value"],
            "author": result["author"]["value"],
            "description": result["description"]["value"],
            "content_type": result["content_type"]["value"],
            "content_provider": result["content_provider"]["value"],
            "link": result["link"]["value"],
            "picture": result["image"]["value"]
        })

    return render_template('show_entries.html', chos=objects) 


if __name__ == '__main__':
    app.run()
