from mwclient import Site
import html2text
from requests import HTTPError
import sys

from discordClient.model.models import *


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
    formatted_description = re.sub(r"''(.*?)''", r"\1", formatted_description)
    formatted_description = re.sub(r"<.*?>.*?<.*?>", r"", formatted_description)
    formatted_description = re.sub(r"===.*?===", r"", formatted_description)
    formatted_description = re.sub(r"==.*?==", r"", formatted_description)
    return formatted_description


if __name__ == '__main__':

    html = html2text.HTML2Text()
    html.ignore_links = True
    html.ignore_images = True
    html.body_width = 0
    characters = []

    start_at = "Star Wars"
    can_start = True
    skip_creation = False

    if not skip_creation:
        site = Site("disney.fandom.com", path="/")
        for page in site.categories["Navboxes"]:
            if page.namespace == 10:  # A template one

                affiliation_name = page.base_title
                print(f"=== Template {affiliation_name} ===")

                if not can_start:
                    if affiliation_name == start_at:
                        can_start = True
                    else:
                        continue

                # DATABASE INSERTION - Affiliation
                try:
                    affiliation_model = Affiliation.get((Affiliation.name == affiliation_name and
                                                         Affiliation.category == "Disney"))
                except DoesNotExist:
                    affiliation_model = Affiliation(name=affiliation_name, category="Disney")
                    affiliation_model.save()
                # DATABASE INSERTION - Affiliation

                wikitext = page.text()
                wikitext = re.search(r"{{.*?}}", wikitext, flags=re.RegexFlag.S).group(0)
                regex_result = re.finditer("\\[\\[(.*?)(\\|.*?)?\\]\\]", wikitext)

                associated_links = []
                for regex in regex_result:  # On parcourt tous les éléments liens de la navbox courante
                    wiki_link = regex.group(1)
                    associated_links.append(regex.group(1))

                # Filtrer sur les personnages uniquement
                characters_to_keep = {}
                while len(associated_links) > 0:
                    links_list = associated_links[:50]
                    del associated_links[:50]
                    keep_going = True
                    cl_continue = ""
                    while keep_going:
                        if cl_continue:
                            result = site.api(action="query", titles="|".join(links_list), prop="categories|info",
                                              cllimit="max", clcontinue=cl_continue)
                        else:
                            result = site.api(action="query", titles="|".join(links_list), prop="categories|info",
                                              cllimit="max")
                        if "continue" in result:
                            keep_going = True
                            cl_continue = result["continue"]["clcontinue"]
                        else:
                            keep_going = False
                        for page_id in result["query"]["pages"]:
                            page = result["query"]["pages"][page_id]
                            if page["title"] not in characters_to_keep:
                                if "categories" in page:
                                    for category in page["categories"]:
                                        if "CHARACTERS" in category["title"].upper():
                                            characters_to_keep[page["title"]] = page

                for character in characters_to_keep:

                    # Character page id
                    character_id = characters_to_keep[character]["pageid"]
                    # Character page id

                    if character_id not in characters:
                        characters.append(character_id)

                        page_data = site.api(action="parse", pageid=character_id, prop="displaytitle|wikitext")
                        wiki_text = page_data["parse"]["wikitext"]["*"]

                        # Character description
                        wiki_text = page_data["parse"]["wikitext"]["*"]
                        informations = extract_informations(wiki_text)
                        i = len(informations) - 1
                        while i >= 0:
                            information = informations[i]
                            wiki_text = wiki_text[0:information["start_index"]] + wiki_text[
                                                                                  information["end_index"]:]
                            i -= 1
                        wiki_text = format_description(wiki_text)
                        api_result = site.api(action="parse", text=wiki_text)
                        wiki_text = api_result["parse"]["text"]["*"]
                        wiki_text = wiki_text.replace("\n", "").replace("<br />", "").replace("<p></p>",
                                                                                              "").strip()
                        character_description = html.handle(wiki_text).replace("\n\n", "\n")
                        # Character description

                        # Character name
                        character_name = page_data["parse"]["displaytitle"]
                        # Character name

                        # Character size
                        character_size = characters_to_keep[character]["length"]
                        # Character size

                        # Character image
                        try:
                            image_data = site.api(action="imageserving", wisId=character_id)
                            character_image_url = ""
                            if "image" not in image_data and "imageserving" not in image_data["image"]:
                                continue
                            else:
                                character_image_url = image_data["image"]["imageserving"]
                        except HTTPError:
                            continue
                        # Character image

                        # DATABASE INSERTION - Character
                        try:
                            character_model = Character.get(
                                (Character.page_id == int(character_id)) & (Character.category == 'Disney'))
                            character_model.description = character_description[:1024]
                            character_model.description_size = character_size
                            character_model.image_link = character_image_url
                            character_model.rarity = -1
                        except DoesNotExist:
                            character_model = Character(name=character_name,
                                                        description=character_description[:1024],
                                                        description_size=character_size,
                                                        category="Disney",
                                                        image_link=character_image_url,
                                                        page_id=int(character_id),
                                                        rarity=-1)
                        finally:
                            character_model.save()
                        # DATABASE INSERTION - Affiliation

                    # DATABASE INSERTION - CharacterAffiliation
                    character_model = Character.get(
                        (Character.page_id == int(character_id)) & (Character.category == 'Disney'))
                    try:
                        character_affiliation_model = (
                            CharacterAffiliation.select()
                                                .where((CharacterAffiliation.character_id == character_model.get_id()) &
                                                       (CharacterAffiliation.affiliation_id == affiliation_model.get_id()))
                                                .get())
                        print("hey")
                    except DoesNotExist:
                        character_affiliation_model = CharacterAffiliation(character_id=character_model.get_id(),
                                                                           affiliation_id=affiliation_model.get_id())
                        character_affiliation_model.save()
                    # DATABASE INSERTION - CharacterAffiliation


    print(f"Number of character {len(characters)}")

    # Rarity assignation
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
    # Rarity assignation
