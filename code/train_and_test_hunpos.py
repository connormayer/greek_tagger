import subprocess

from collections import defaultdict
from xml.etree import ElementTree

TRAIN_SET = "hunpos_data/hunpos_greek_train_{}.pos"
TEST_SET = "hunpos_data/hunpos_greek_test_{}.pos"
HUNPOS_MODEL = "hunpos_models/model_{}"
# HUNPOS_MORPH = "morpheus.pos"
HUNPOS_MORPH = "morpheus_cheating.pos"
RESULTS = "hunpos_data/results/results_{}.txt"
ANSWERS = "hunpos_data/answers/hunpos_greek_answers_{}.pos"

X_FOLD = 10

def train_and_test():
    for i in range(X_FOLD):
        print("Training fold {}...".format(i))
        train_cat = subprocess.Popen(
            ('cat', TRAIN_SET.format(i)), stdout=subprocess.PIPE
        )
        train_data, _ = train_cat.communicate()

        train = subprocess.Popen(
            ('hunpos/trainer.native', HUNPOS_MODEL.format(i)),
            stdin=subprocess.PIPE
        )
        train.communicate(input=train_data)

        print("Testing fold {}...".format(i))
        test_cat = subprocess.Popen(
            ('cat', TEST_SET.format(i)), stdout=subprocess.PIPE
        )
        test_data, _ = test_cat.communicate()

        with open(RESULTS.format(i), 'w') as output:
            test = subprocess.Popen(
                ('hunpos/tagger.native', HUNPOS_MODEL.format(i),
                 '-m', HUNPOS_MORPH.format(i)),
                 #),
                stdin=subprocess.PIPE, stdout=output
            )
            test.communicate(input=test_data)

def check_accuracies():
    correct_percents = []
    wrong_answers = []

    for i in range(X_FOLD):
        total_right = 0
        total = 0
        with open(ANSWERS.format(i), 'r') as answers_file:
            with open(RESULTS.format(i)) as results_file:
                answers = [
                line for line in answers_file if not line.isspace()
                and line.split('\t')[0]]
                results = [line for line in results_file if not line.isspace()]
                for answer, result in zip(answers, results):
                    total += 1
                    answer_word, answer_pos = answer.split('\t')[:2]
                    result_word, result_pos = result.split('\t')[:2]
                    answer_pos = answer_pos.rstrip()
                    result_pos = result_pos.rstrip()

                    if answer_pos != result_pos:
                        wrong_answers.append([answer_word, answer_pos, result_pos])
                    else:
                        total_right +=1
                correct_percents.append(total_right/total)
    
    output_dict = defaultdict(list)

    with open(HUNPOS_MORPH, 'r') as morph_file:
        for line in morph_file:
            line_list = line.rstrip().split('\t')
            output_dict[line_list[0]] = line_list[1:]

    inconsistent_tags = 0

    for answer in wrong_answers:
        # print(answer)
        parse = output_dict.get(answer[0])
        if parse:
            if answer[1] not in parse:
                inconsistent_tags += 1
    #             print("{}:\nPossible M tags: {}\nSuggested tag: {}\nCorrect tag: {}".format(
    #                 answer[0], parse, answer[1], answer[2]))
    # print(inconsistent_tags)
    print(correct_percents)
    print(sum(correct_percents) / len(correct_percents))

if __name__ == "__main__":
    train_and_test()
    check_accuracies()