import requests
import re
from discordClient.model.models import *

default_url = "https://disney.fandom.com/api.php?action=query&list=categorymembers&cmtitle=Category:Disney_characters&format=json&cmlimit=500{}"
page_url = "https://disney.fandom.com/api.php?action=parse&format=json&pageid={}&prop=images|displaytitle|properties|parsewarnings|wikitext"
image_url = "https://disney.fandom.com/api.php?action=imageserving&wisId={}&format=json"


def extract_informations(text: str):
    nbr_accolade = 0
    informations = []
    char_index = 0

    start_index = -1
    start_name = -1
    end_name = -1

    for character in text:
        if character == '{':
            nbr_accolade += 1
            if nbr_accolade == 1:
                start_index = char_index
            elif nbr_accolade == 2 and start_name == -1:
                start_name = char_index + 1
        elif character == '}':
            nbr_accolade -= 1
            if nbr_accolade == 0:
                informations.append({"start_index": start_index, "end_index": char_index + 1,
                                     "content": text[start_index + 2:char_index - 1],
                                     "name": text[start_name:end_name]})
                start_index = -1
                start_name = -1
                end_name = -1
        elif character == '|' and end_name == -1 and start_index != -1:
            end_name = char_index

        char_index += 1

    return informations


def format_description(unformatted_description):
    formatted_description = unformatted_description
    formatted_description = re.sub(r"\[\[(.*?)(?:\|(.*?))?\]\]", r"\1", formatted_description)
    formatted_description = re.sub(r"''(.*?)''", r"\1", formatted_description)
    formatted_description = re.sub(r"<.*?>.*?<.*?>", r"", formatted_description)
    return formatted_description


def extract_datas(key, dictionary):
    ret_value = []
    if key in dictionary:
        key_content = dictionary[key]
        re_objects = re.finditer(r"\[\[(.*?)(?:\|(.*?))?\]\]", key_content)
        for re_object in re_objects:
            ret_value.append(re_object.group(1))
    return ret_value


def create_feature(feature_name, feature_type):
    try:
        feature_model = Feature.get((Feature.name == feature_name) & (Feature.type == feature_type))
    except DoesNotExist:
        feature_model = Feature(name=feature_name,
                                type=feature_type)
        feature_model.save()
    finally:
        return feature_model


if __name__ == '__main__':
    is_over = True
    cm_continue = ""
    keys_to_check = ("films", "shorts", "shows", "games", "rides")
    keys_to_check_set = set(keys_to_check)
    while not is_over:
        request_url = default_url.format(cm_continue)
        print("Execution request {}".format(request_url))
        json_response = requests.get(request_url).json()
        if 'continue' in json_response:
            cm_continue = "&cmcontinue={}".format(json_response['continue']['cmcontinue'])
        else:
            is_over = True
        for character_json in json_response['query']['categorymembers']:
            page_id = character_json["pageid"]

            page_request_url = page_url.format(page_id)
            page_response = requests.get(page_request_url).json()

            # Définition des valeurs par défaut pour le personnage
            character_name = page_response['parse']['title']
            character_description = "No description found."
            character_category = "Disney"

            wiki_text = page_response['parse']['wikitext']['*']

            informations = extract_informations(wiki_text)

            # Recherche si on conserve le personnage ou non
            i = len(informations) - 1
            character_kept = False

            wiki_dict = {}
            while i >= 0:
                information = informations[i]
                if "Infobox character" in information['name']:
                    infobox_character = information['content']
                    for element in infobox_character.split('\n|'):
                        if " = " in element:
                            element_split = element.split('=')
                            wiki_dict[element_split[0].replace('|', '').strip()] = element_split[1].strip()
                    wiki_dict_set = set(wiki_dict)
                    if keys_to_check_set.intersection(wiki_dict_set):
                        if "name" in wiki_dict:
                            temp_character_name = wiki_dict['name'].split("<br>")[0]
                            if temp_character_name:
                                character_name = wiki_dict['name'].split("<br>")[0]
                        character_kept = True

                wiki_text = wiki_text[0:information["start_index"]] + wiki_text[information["end_index"]:]
                i -= 1

            # On evite les noms de personnages vides, cela n'a aucun sens
            if not character_name:
                continue

            # Le personnage est conservé
            if character_kept:

                # Récupération de la description
                wiki_text = wiki_text.strip()
                wiki_text_split = wiki_text.split("\n")
                if "==Background==" in wiki_text_split:
                    index_bg = wiki_text_split.index("==Background==")
                    if not wiki_text_split[index_bg + 1].startswith("=="):
                        character_description = format_description(wiki_text_split[index_bg + 1])
                    else:
                        character_description = format_description(wiki_text_split[0])
                else:
                    character_description = format_description(wiki_text_split[0])

                # Récupération de l'image url
                image_request_url = image_url.format(character_json["pageid"])
                image_response = requests.get(image_request_url).json()
                if "image" in image_response:
                    character_url = image_response["image"]["imageserving"]
                else:
                    continue

                # Récupération des differentes apparations du personnage
                films = extract_datas("films", wiki_dict)
                shorts = extract_datas("shorts", wiki_dict)
                shows = extract_datas("shows", wiki_dict)
                games = extract_datas("games", wiki_dict)
                rides = extract_datas("rides", wiki_dict)

                # Récupération des affiliations
                affiliations = extract_datas("affiliations", wiki_dict)

                ######################
                # Création des classes
                # Character
                try:
                    character_model = Character.get((Character.page_id == page_id) & (Character.category == 'Disney'))
                except DoesNotExist:
                    character_model = Character(name=character_name,
                                                description=character_description,
                                                description_size=len(wiki_text),
                                                category=character_category,
                                                image_link=character_url,
                                                page_id=page_id,
                                                rarity=-1)
                    character_model.save()

                # Features
                feature_models = []
                for film in films:
                    feature_models.append(create_feature(film, "films"))

                for short in shorts:
                    feature_models.append(create_feature(short, "shorts"))

                for show in shows:
                    feature_models.append(create_feature(show, "shows"))

                for game in games:
                    feature_models.append(create_feature(game, "games"))

                for ride in rides:
                    feature_models.append(create_feature(ride, "rides"))

                # Affiliations
                affiliations_model = []
                for affiliation_name in affiliations:
                    try:
                        affiliation_model = Affiliation.get((Affiliation.name == affiliation_name))
                    except DoesNotExist:
                        affiliation_model = Affiliation(name=affiliation_name)
                        affiliation_model.save()
                    finally:
                        affiliations_model.append(affiliation_model)

                # CharacterOccurence
                for feature in feature_models:
                    try:
                        occurrence_model = CharacterOccurrence.get(
                            (CharacterOccurrence.character_id == character_model.get_id()) &
                            (CharacterOccurrence.feature_id == feature.get_id()))
                    except DoesNotExist:
                        occurrence_model = CharacterOccurrence(character_id=character_model.get_id(),
                                                               feature_id=feature.get_id())
                        occurrence_model.save()

                for affiliation in affiliations_model:
                    try:
                        affiliation_model = CharacterAffiliation.get(
                            (CharacterAffiliation.character_id == character_model.get_id()) &
                            (CharacterAffiliation.affiliation_id == affiliation.get_id()))
                    except DoesNotExist:
                        affiliation_model = CharacterAffiliation(character_id=character_model.get_id(),
                                                                 affiliation_id=affiliation.get_id())
                        affiliation_model.save()

                print("Character created {}!".format(character_model.name))

    index = 1
    total = Character.select().count()
    rarities = [50, 25, 12.5, 9, 3, 0.5]
    current_rarity = 0
    rarity_index = 0
    for character in Character.select().order_by(Character.description_size):
        percent = (index / total) * 100
        if percent > current_rarity:
            current_rarity += rarities[rarity_index]
            rarity_index += 1
        character.rarity = rarity_index
        character.save()
        index += 1


