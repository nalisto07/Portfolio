import markdown
import requests
import math
from PIL import Image, ImageDraw

def get_node(open_id: int)->dict:
    '''Fonction qui effectue une requête vers l'api openstreetmap
    et qui renvoie le résultat de cette requête sous forme d'un dictionnaire json.'''
    api_url = f'https://api.openstreetmap.org/api/0.6/node/{open_id}.json'
    response = requests.get(api_url)
    code = response.status_code
    if code == 200:
        dicoJson=response.json() #Variable contient dictionnaire directement en json 
        return dicoJson        
    else:
        return "Il y a une erreur !", code
    

def node_to_md(data: dict, filename:str)->None:
    '''Fonction qui récupère des informations à partir du dictionnaire json
    et qui les écrits dans un fichier .md'''
    with open(filename, 'w') as f:
        # écrire le nom dans le fichier md :
        element = data['elements'][0]
        tag = element['tags']
        if 'tags' in element:
            name = tag.get('name') #Utilisation du .get() prend la clé 'name' dans le dico tags et ne renvoie pas d'erreur même si il n'y a pas de noms
        else:
            name =  "SANS NOM"
        f.write(f"# {name}\n")
        id = element.get('id')
        f.write(f"## [lien](https://api.openstreetmap.org/node/{id})\n")
        # écrire le contenu du dico :
        for cle, val in element.items():
            if cle == "tags":
                break
            f.write(f"- {cle} : {val}\n")
        f.write(f"\n")
        f.write(f"# Contenu des tags \n")
        f.write(f"\n")
        for cle, val in tag.items():
            f.write(f"- {cle} : {val}\n")

        lat = element.get('lat')
        lon = element.get('lon')
        carte = generate_map(lat, lon)
        f.write(carte)

def deg2num(lat, lon, zoom=15) -> tuple[int, int]:
    '''Fonction qui traduit les latitudes et longitudes récupérées en coordonnées de tuiles
    pour pouvoir télécharger la bonne tuile '''
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

# Génération de la carte avec marqueur
def generate_map(lat, lon, zoom=15):
    """Télécharge une tuile OSM et ajoute un marqueur au centre"""

    xtile, ytile = deg2num(lat, lon, zoom)
    headers = {'User-Agent': 'SAE105_Etudiant'}
    url = f"https://a.tile.openstreetmap.fr/osmfr/{zoom}/{xtile}/{ytile}.png"
    response = requests.get(url, headers=headers)
    filename = "carte.png"
    if response.status_code == 200:
        with open(filename, "wb") as f:# écrire avec wb car w ne prend pas en charge les images
            f.write(response.content)# écrit les bytes  contenus dans response
        carte = Image.open(filename).convert("RGB")
        d = ImageDraw.Draw(carte)
        r = 5 # rayon du pointeur
        x= 128 # coordonnées du pointeur au centre 256/2
        y = 128
        d.ellipse([x - r, y - r, x + r, y + r], fill="red", outline="black")
        carte.save(filename)
        return "\n![Carte](carte.png)"

    else:
        return "Carte introuvable"

#Focntion pour convertir le contenu du md en html
def convert(fichier1, fichier2)->None:
    '''Fonction pour convertir un fichier .md en fichier .html'''
    with open(fichier1, 'r') as f:
        text = f.read()
    html = markdown.markdown(text)
    html2 = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fiche OSM</title>
</head>
<body>
{html}
</body>
</html>
'''
    with open(fichier2, 'w', encoding = 'utf-8') as f:
        f.write(html2)

def fiche_osm(id:int)->None:
    '''Fonction qui va afficher les informations sur un noeud OSM sur une page html
    à partir d'un id openstreeetmap.'''
    get_node(id)
    node_to_md(data = get_node(id), filename = 'osm.md')
    convert(fichier1='osm.md',fichier2='osm.html')
    print('fini')

###################################################################

import requests
import markdown

def get_dataset(query:str)->dict:
    '''Fonction qui effectue une requête au près de l'api et va récupérer un dictionnaire au format Json.'''
    api_url = 'https://overpass-api.de/api/interpreter'
    response = requests.post(api_url, data = {'data':query})
    code = response.status_code
    marque = []
    reponse = response.json()
    element = reponse["elements"]
    if code == 200:
        for i in element:
            tag = i['tags']
            if 'brand' in tag:
                marque.append(tag['brand'])
            if 'brand' not in tag:
                marque.append("Sans Nom")
        return response.json() #Variable contient dictionnaire directement en json        
    else:
        return "Il y a une erreur !", code
    
def compute_statistics(dico:dict)->dict:
    '''Fonction qui va récupérer les différentes marques de voitures dans la zone 
    entrée par la requête, qui crée un dictionnaire avec le nombre de fois que la marque est présente
    dans une zone. Enfin la fonction récupére le résultat du dictionnaire et va le transformer sous la forme 
    d'un autre dictionnaire mais avec des pourcentages.'''
    marque = []
    reponse = dico # réponse prend la valeur du dico.json() de la fonction get_dataset
    element = reponse["elements"] #élément prend la valeur de la liste 'éléments' du dictionnaire réponse
    # Récupere la marque avec l'attribut 'brand' si il est présent dans tag
    for i in element:
        tag = i['tags']
        if 'brand' in tag:
            marque.append(tag['brand'])
        if 'brand' not in tag:
            marque.append("Sans Nom")
    # Création d'un dictionnaire qui compte le nb de marques
    dico = {}
    for j in range(len(marque)):
        if marque[j] in dico:
            dico[marque[j]]+=1
        else:
            dico[marque[j]] = 1
    # Création nv_dico qui transforme le nombre précédent en un pourcentage
    total = len(marque)
    nv_dico = {}
    for cle, val in dico.items():
        stat = 0
        stat = (val/total)*100
        nv_dico[cle] = stat
    # Trie le dictionnaire pour que les pourcentages s'affichent dans l'ordre croissant
    nv_dico = dict(sorted(nv_dico.items(), key=lambda item: item[1], reverse = True))
    return nv_dico

        
def data_set_to_md(dataset:dict, filename:str)->None:
    '''Fonction qui permet d'écrire dans un fichier .md
    les infos du dictionnaire, ainsi que les statistiques voulues'''
    with open(filename, 'w') as f:
        element = dataset['elements']
        f.write("# Requête effectuée :\n")
        f.write(f"- {req}\n")
        f.write("# Pourcentage de marques recensé dans la région :\n")
        statistique = compute_statistics(dataset)
        for cle, val in statistique.items():
            f.write(f"- **{cle}**: {val}%\n")
        f.write("# Liste des Garages :\n")
        # écrire les noms suivis de leurs informations recensées :
        for i in element:
            tag = i['tags']
            if 'name' in tag:
                name = tag.get('name') #Utilisation du .get() prend la clé 'name' dans le dico tags et ne renvoie pas d'erreur même si il n'y a pas de noms
            else:
                name =  "SANS NOM"
            f.write(f"## {name}\n")
            
            for cle,val in tag.items():
                f.write(f"- **{cle}**: {val}\n\n")
        
def convert(fichier1, fichier2)->None:
    '''Fonction pour convertir un fichier .md en fichier .html'''
    with open(fichier1, 'r') as f:
        text = f.read()
    html = markdown.markdown(text)
    html2 = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fiche OSM</title>
</head>
<body>
{html}
</body>
</html>
'''
    with open(fichier2, 'w', encoding = 'utf-8') as f:
        f.write(html2)

def info_locales(dataset:dict)->None:
    '''Fonction qui permet d'afficher sur une page html les statistiques des différents garages
    présents dans une région donnée, ainsi que toutes leurs informations qui sont recensées sur overpass-turbo'''
    compute_statistics(get_dataset(req))
    data_set_to_md(dataset, 'stat.md')
    convert('stat.md', 'stat.html')
    print("fini")
# requête 
req="""
    [out:json][timeout:25];
    area["wikipedia"="fr:Paris"]->.zone_de_recherche;
    (
    node["shop"="car"](area.zone_de_recherche);
    nwr["shop"="car"](area.zone_de_recherche);
    );
    out geom;
    """

    



