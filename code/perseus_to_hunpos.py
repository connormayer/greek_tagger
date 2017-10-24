import math
import numpy

from os import listdir
from os.path import isfile, join
from xml.etree import ElementTree

PERSEUS_DIR = '../corpora/treebank_data/v2.1/Greek/texts'
HUNPOS_FILE = "hunpos_data/hunpos_greek_training.pos"
TRAINING_FILES = "hunpos_data/hunpos_greek_train_{}.pos"
TEST_FILES = "hunpos_data/hunpos_greek_test_{}.pos"
ANSWER_FILES = "hunpos_data/answers/hunpos_greek_answers_{}.pos"

X_FOLD = 10

def convert_perseus_training_to_hunpos():
    pos_set = []
    files = [
        join(PERSEUS_DIR, f) for f in listdir(PERSEUS_DIR)
        if isfile(join(PERSEUS_DIR, f))
    ]

    for file in files:
        xml_doc = ElementTree.parse(file).getroot().find('body')
        for sentence in xml_doc.findall('sentence'):
            line = []
            for word in sentence.findall('word'):
                # TODO: Figure out these weird words
                if not 'insertion_id' in word.keys():
                    try:
                        word_str = word.get('form').replace(' ', '') + '/' + word.get('postag')
                        line.append(word_str)
                    except:
                        import pdb; pdb.set_trace()
            line.append('<s>')
            pos_set.append(' '.join(line))

    sentence_count = len(pos_set)
    tenth = math.ceil(int(sentence_count) / int(10))

    ten_parts = []
    for i in range(X_FOLD):
        try:
            chunk = numpy.random.choice(pos_set, tenth, False)
            pos_set = [sentence for sentence in pos_set if not sentence in chunk]
        except ValueError:
            chunk = pos_set
    
        ten_parts.append(chunk)

    for i in range(X_FOLD):
        test_set = ten_parts[i]

        # filter out this loop's test index
        training_set_lists = [
            x for x in ten_parts if x is not ten_parts[i]
        ]

        # next concatenate the list together into 1 file
        # ( http://stackoverflow.com/a/952952 )
        training_set = [
            item for sublist in training_set_lists for item in sublist
        ]

        with open(TRAINING_FILES.format(i), 'w') as train_file:
            for line in training_set:
                words = line.split(' ')
                for word in words:
                    try:
                        form, pos = word.split('/')
                    except:
                        form, pos = word, ''
                    print(
                        "{}\t{}".format(form, pos), 
                        file=train_file
                    )

        with open(TEST_FILES.format(i), 'w') as test_file:
            with open(ANSWER_FILES.format(i), 'w') as answer_file:
                for line in test_set:
                    words = line.split(' ')
                    for word in words:
                        try:
                            form, pos = word.split('/')
                        except:
                            form, pos = word, ''
                        print(
                            "{}".format(form), 
                            file=test_file
                        )
                        print(
                            "{}\t{}".format(form, pos),
                            file=answer_file
                        )

if __name__ == "__main__":
    convert_perseus_training_to_hunpos()
