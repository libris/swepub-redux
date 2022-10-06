import csv

print("@prefix uka: <https://id.kb.se/term/uka/> .")
print("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")

with open("uka_terms.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
    for row in reader:
        data = { k:v.strip() for k, v in row.items()}
        if data["level1"]:
            print(f"""
uka:{data['level1']} a skos:Concept ;
    skos:inScheme uka: ;
    skos:prefLabel "{data["en"]}"@en,
        "{data["sv"]}"@sv .""")
        if data["level2"]:
            print(f"""
uka:{data['level2']} a skos:Concept ;
    skos:inScheme uka: ;
    skos:broader uka:{data["level2"][:1]} ;
    skos:prefLabel "{data["en"]}"@en,
        "{data["sv"]}"@sv .""")
        if data["level3"]:
            print(f"""
uka:{data['level3']} a skos:Concept ;
    skos:inScheme uka: ;
    skos:broader uka:{data["level3"][:3]} ;
    skos:prefLabel "{data["en"]}"@en,
        "{data["sv"]}"@sv .""")       
