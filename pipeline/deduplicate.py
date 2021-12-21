import os
import json
import re

stopwords = {"aderton", "adertonde", "adjö", "aldrig", "alla", "allas", "allt", "alltid", "alltså", "än", "andra", "andras", "annan", "annat", "ännu", "artonde", "artonn", "åtminstone", "att", "åtta", "åttio", "åttionde", "åttonde", "av", "även", "båda", "bådas", "bakom", "bara", "bäst", "bättre", "behöva", "behövas", "behövde", "behövt", "beslut", "beslutat", "beslutit", "bland", "blev", "bli", "blir", "blivit", "bort", "borta", "bra", "då", "dag", "dagar", "dagarna", "dagen", "där", "därför", "de", "del", "delen", "dem", "den", "deras", "dess", "det", "detta", "dig", "din", "dina", "dit", "ditt", "dock", "du", "efter", "eftersom", "elfte", "eller", "elva", "en", "enkel", "enkelt", "enkla", "enligt", "er", "era", "ert", "ett", "ettusen", "få", "fanns", "får", "fått", "fem", "femte", "femtio", "femtionde", "femton", "femtonde", "fick", "fin", "finnas", "finns", "fjärde", "fjorton", "fjortonde", "fler", "flera", "flesta", "följande", "för", "före", "förlåt", "förra", "första", "fram", "framför", "från", "fyra", "fyrtio", "fyrtionde", "gå", "gälla", "gäller", "gällt", "går", "gärna", "gått", "genast", "genom", "gick", "gjorde", "gjort", "god", "goda", "godare", "godast", "gör", "göra", "gott", "ha", "hade", "haft", "han", "hans", "har", "här", "heller", "hellre", "helst", "helt", "henne", "hennes", "hit", "hög", "höger", "högre", "högst", "hon", "honom", "hundra", "hundraen", "hundraett", "hur", "i", "ibland", "idag", "igår", "igen", "imorgon", "in", "inför", "inga", "ingen", "ingenting", "inget", "innan", "inne", "inom", "inte", "inuti", "ja", "jag", "jämfört", "kan", "kanske", "knappast", "kom", "komma", "kommer", "kommit", "kr", "kunde", "kunna", "kunnat", "kvar", "länge", "längre", "långsam", "långsammare", "långsammast", "långsamt", "längst", "långt", "lätt", "lättare", "lättast", "legat", "ligga", "ligger", "lika", "likställd", "likställda", "lilla", "lite", "liten", "litet", "man", "många", "måste", "med", "mellan", "men", "mer", "mera", "mest", "mig", "min", "mina", "mindre", "minst", "mitt", "mittemot", "möjlig", "möjligen", "möjligt", "möjligtvis", "mot", "mycket", "någon", "någonting", "något", "några", "när", "nästa", "ned", "nederst", "nedersta", "nedre", "nej", "ner", "ni", "nio", "nionde", "nittio", "nittionde", "nitton", "nittonde", "nödvändig", "nödvändiga", "nödvändigt", "nödvändigtvis", "nog", "noll", "nr", "nu", "nummer", "och", "också", "ofta", "oftast", "olika", "olikt", "om", "oss", "över", "övermorgon", "överst", "övre", "på", "rakt", "rätt", "redan", "så", "sade", "säga", "säger", "sagt", "samma", "sämre", "sämst", "sedan", "senare", "senast", "sent", "sex", "sextio", "sextionde", "sexton", "sextonde", "sig", "sin", "sina", "sist", "sista", "siste", "sitt", "sjätte", "sju", "sjunde", "sjuttio", "sjuttionde", "sjutton", "sjuttonde", "ska", "skall", "skulle", "slutligen", "små", "smått", "snart", "som", "stor", "stora", "större", "störst", "stort", "tack", "tidig", "tidigare", "tidigast", "tidigt", "till", "tills", "tillsammans", "tio", "tionde", "tjugo", "tjugoen", "tjugoett", "tjugonde", "tjugotre", "tjugotvå", "tjungo", "tolfte", "tolv", "tre", "tredje", "trettio", "trettionde", "tretton", "trettonde", "två", "tvåhundra", "under", "upp", "ur", "ursäkt", "ut", "utan", "utanför", "ute", "vad", "vänster", "vänstra 	var", "vår", "vara", "våra", "varför", "varifrån", "varit", "varken", "värre", "varsågod", "vart", "vårt", "vem", "vems", "verkligen", "vi", "vid", "vidare", "viktig", "viktigare", "viktigast", "viktigt", "vilka", "vilken", "vilket", "vill", "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in", "into", "is", "it", "no", "not", "of", "on", "or", "such", "that", "the", "their", "then", "there", "these", "they", "this", "to", "was", "will", "with"}    

def deduplicate():

    # map from oai_id -> record, for all of swepub (it isn't large, and fits in memory)
    records_by_id = {}

    # map words (found within each publications main title), to lists of oai_ids
    # of the records containing those words.
    index = {}
    
    for entry in os.scandir('./output/raw/'):
        if entry.is_file():
            with open(entry, "r") as f:
                for line in f.readlines():
                    record = json.loads(line)

                    # The oai-id
                    records_by_id[record["@id"]] = record

                    # For each word in the title
                    for title in record["instanceOf"]["hasTitle"]:
                        for word in re.findall(r"\w+", title["mainTitle"]):
                            lowcaseword = str.lower(word)
                            if not lowcaseword in stopwords:
                                if not lowcaseword in index:
                                    index[lowcaseword] = [] 
                                index[lowcaseword].append(record["@id"])

    for oai_id, record in records_by_id.items():
        candidate_duplicates = [oai_id]

        for title in record["instanceOf"]["hasTitle"]:
            for word in re.findall(r"\w+", title["mainTitle"]):
                lowcaseword = str.lower(word)
                if not lowcaseword in stopwords:
                    for candidate_id in index[lowcaseword]:
                        candidate_duplicates.append(candidate_id)

        if len(candidate_duplicates) > 1:
            print(f"check for dups: {len(candidate_duplicates)}")
                    

# TEMP
deduplicate()
