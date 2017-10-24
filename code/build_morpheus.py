import json
import requests
import string

from collections import defaultdict
from os import listdir
from os.path import isfile, join
from xml.etree import ElementTree

MORPHEUS_URL = "http://morph.perseids.org/analysis/word?lang=grc&engine=morpheusgrc&word={}"
HEADERS = {'Accept': 'application/json'}
PERSEUS_DIR = '../corpora/treebank_data/v2.1/Greek/texts'
PARSE_FILE = 'morpheus.pos'
FAILED_FILE = 'failures.txt'
MISSED_FILE = 'misses.txt'
BROKEN_FILE = 'broken.txt'

POS = {
    'adjective': 'a',
    'noun': 'n',
    'verb': 'v',
    'verb participle': 'v',
    # Why are there two markings for adv?
    'adverb': 'd',
    'adverbial': 'd', 
    'article': 'l',
    'particle': 'g',
    'preposition': 'r',
    'pronoun': 'p',
    'numeral': 'm',
    'conjunction': 'c',
    'irregular': 'x',
    'exclamation': 'i'
    # Interjection?
    # Punctuation?  
}

PERSON = {
    '1st': '1',
    '2nd': '2',
    '3rd': '3'
}

NUMBER = {
    'singular': 's',
    'plural': 'p',
    'dual': 'd'
}

TENSE = {
    'present': 'p',
    'imperfect': 'i',
    'perfect': 'r',
    'pluperfect': 'l',
    'future perfect': 't',
    'future': 'f',
    'aorist': 'a'
}

MOOD = {
    'indicative': 'i',
    'subjunctive': 's',
    'optative': 'o',
    'infinitive': 'n',
    'imperative': 'm',
    'participle': 'p'
}

VOICE = {
    'active': 'a',
    'passive': 'p',
    'middle': 'm',
    'mediopassive': 'e',       
}

GENDER = {
    'masculine': 'm',
    'feminine': 'f',
    'neuter': 'n'
}

CASE = {
    'nominative': 'n',
    'genitive': 'g',
    'dative': 'd',
    'accusative': 'a',
    'vocative': 'v',
    # Morpheus doesn't seem to include the locative case.
    'locative': 'l'
}

DEGREE = {
    'comparative': 'c',
    'superlative': 's'
}

DICT_LIST = [
    ['pofs', POS],
    ['pers', PERSON],
    ['num', NUMBER],
    ['tense', TENSE],
    ['mood', MOOD],
    ['voice', VOICE],
    ['gend', GENDER],
    ['case', CASE],
    ['comp', DEGREE]
]

def make_morpheus():
    with open(PARSE_FILE, 'a+') as pf:
        pf.seek(0)
        completed_parses = [line.split('\t')[0] for line in pf]
    with open(FAILED_FILE, 'a+') as ff:
        ff.seek(0)
        failed_lookups = [word.rstrip() for word in ff]
    with open(BROKEN_FILE, 'a+') as bf:
        bf.seek(0)
        failed_lookups.extend([word.rstrip() for word in bf])

    files = [
        join(PERSEUS_DIR, f) for f in listdir(PERSEUS_DIR)
        if isfile(join(PERSEUS_DIR, f))
    ]

    for file in files:
        xml_doc = ElementTree.parse(file).getroot()

        words = []
        for sentence in xml_doc.find('body').findall('sentence'):
            words.extend(sentence.findall('word'))

        for word_xml in words:
            word = word_xml.get('form')
            perseus_pos = word_xml.get('postag')

            if word in completed_parses or word in failed_lookups:
                # Already have this word
                continue

            print("LOOKING UP: {}".format(word))
            req = requests.get(
                MORPHEUS_URL.format(word), headers=HEADERS
            )
            try:
                req_json = json.loads(req.text)
            except:
                # Some words seem to break the server, unicode issue?
                with open(BROKEN_FILE, 'a+') as bf:
                    print(word, file=bf)
                    continue
            
            try:
                analyses = req_json['RDF']['Annotation']['Body']
            except:
                # No results
                if word in string.punctuation and word not in completed_parses:
                    completed_parses.append(word)
                    with open(PARSE_FILE, 'a+') as pf:
                        print(
                            "{}\t{}".format(word, 'u--------'),
                            file=pf
                        )
                else:
                    failed_lookups.append(word)
                    with open(FAILED_FILE, 'a+') as ff:
                        print(word, file=ff)
                continue

            # Morpheus returns a list if there's more than one possible
            # lemma, but a dict if there's only one...
            if type(analyses) == dict:
                analyses = [analyses]

            pos_list = []

            for analysis in analyses:
                pos_info = analysis['rest']['entry']['infl']
                # Ditto for different inflections of the same word.
                if type(pos_info) == dict:
                    pos_info = [pos_info]

                for infl in pos_info:
                    pos_str = ''
                    for key, mapping in DICT_LIST:
                        entry = infl.get(key)
                        try:
                            pos_str += mapping[entry['$']] if entry else '-'
                        except:
                            if infl.get('gend') and infl.get('gend')['$'] == 'adverbial':
                                pos_str = 'd--------'
                                break
                    pos_list.append(pos_str)

            if perseus_pos not in pos_list:
                with open(MISSED_FILE, 'a+') as mf:
                    print(
                        "{}\t{}\t{}".format(
                            word, perseus_pos, ','.join(pos_list)
                        ),
                        file=mf
                    )

            completed_parses.append(word)
            with open(PARSE_FILE, 'a+') as pf:
                print(
                    "{}\t{}".format(word, '\t'.join(pos_list)),
                    file=pf
                )

def redo_broken():
    parse_dict = []
    broken = []

    with open(PARSE_FILE, 'r') as pf:
        for line in pf:
            line_list = line.rstrip().split('\t')
            parse_dict[line_list[0]] = line_list[1:]

    words = []
    with open(BROKEN_FILE, 'r') as bf:
        for word in bf:
            words.append(word.rstrip())
        bf.truncate()

    for word in words:
        req = requests.get(
            MORPHEUS_URL.format(word), headers=HEADERS
        )
        try:
            req_json = json.loads(req.text)
        except:
            # Some words seem to break the server,
            # unicode issue?
            with open(BROKEN_FILE, 'a+') as bf:
                print(word, file=bf)
                continue


if __name__ == "__main__":
    make_morpheus()