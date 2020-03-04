#!/usr/bin/python
# encoding: utf-8

import sys

# Workflow3 supports Alfred 3's new features. The `Workflow` class
# is also compatible with Alfred 2.
from workflow import Workflow, web
TITLE_WIDTH = 50

def query_oxford(logger, word_id, endpoint="entries", language=u"en-us"):
    url = "https://od-api.oxforddictionaries.com/api/v2/{}/{}/{}".format(
        endpoint, language, word_id)
    try:    
        with open("credentials", "r") as f:
            app_id = f.readline().strip()
            app_key = f.readline().strip()
    except Exception as err:
        logger.exception(err)
        logger.error("Failed to load credentials. Please add your credentials to /credentials")
    try:
        logger.info("Accessing: {} ".format(url))
        results = web.get(url, headers={"app_id": app_id, "app_key": app_key})
        logger.info("Response code: {}".format(results.status_code))
        return results.json()['results']
    except Exception as err:
        logger.exception(err)
        return None
    

def parse_results(wf, results):
    for headword_entry in results:
        headword_type = headword_entry["type"]
        for lexical_entry in headword_entry["lexicalEntries"]:
            for entry in lexical_entry["entries"]:
                for sense in entry["senses"]:
                    if "definitions" not in sense and "translations" not in sense:
                        continue
                    if "translations" in sense:
                        title = ", ".join(translation["text"] for translation in sense["translations"])
                    if "definitions" in sense:
                        title = ", ".join(sense["definitions"])
                    subtitle = lexical_entry["lexicalCategory"]["text"]
                    if "domains" in sense:
                        subtitle += ", " + ", ".join(domain["text"] for domain in sense["domains"])
                    subtitle = title[TITLE_WIDTH:] + subtitle
                    title = title[:TITLE_WIDTH]
                    wf.add_item(title, subtitle, arg=lexical_entry["text"], valid=True)

def possible_lemmas(logger, word_id):
    results = query_oxford(logger, word_id, "lemmas")
    to_return = []
    if results is not None:
        for head_entry in results:
            for lexical_entry in head_entry["lexicalEntries"]:
                for inflection in lexical_entry["inflectionOf"]:
                    to_return.append(inflection["text"])
    logger.info("Possible lemmas: {}".format(" ".join(to_return)))
    return to_return

def translate(wf, word_id, target_lang=u"zh"):
    source_lang=u"en"
    results = query_oxford(wf.logger, u"{}/{}?strictMatch=false".format(target_lang, word_id), u"translations", source_lang)
    wf.logger.info(results)
    if results is not None:
        parse_results(wf, results)
    
def main(wf):
    # Get args from Workflow3, already in normalized Unicode.
    # This is also necessary for "magic" arguments to work.
    args = wf.args
    
    results = query_oxford(wf.logger, args[0])
    word = args[0]
    if results is not None:
        parse_results(wf, results)
    else:
        word = possible_lemmas(wf.logger, word)[0]
        wf.add_item("Using 'root' form: {}".format(word), "", valid=True)
        parse_results(wf, query_oxford(wf.logger, word))

    translate(wf, word)
     
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
