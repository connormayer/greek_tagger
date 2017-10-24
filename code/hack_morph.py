from collections import defaultdict

HUNPOS_MORPH = "morpheus.pos"
CHEAT_MORPH = "morpheus_cheating.pos"
TRAIN_SET = "hunpos_data/hunpos_greek_train_{}.pos"

# Cheats by building a morphological dictionary that only 
# includes the POS that are present in the labeled training
# set.

existing_parses = defaultdict(list)
with open(HUNPOS_MORPH, 'r') as hm:
    for line in hm:
        line_list = line.rstrip().split('\t')
        existing_parses[line_list[0]] = line_list[1:]

existing_parses = defaultdict(list)

for i in range(10):
    with open(TRAIN_SET.format(i), 'r') as f:
        for line in f:
            if "<s>" in line:
                continue
            line_list = line.rstrip().split('\t')
            try:
                if line_list[1] not in existing_parses[line_list[0]]:
                    existing_parses[line_list[0]].append(line_list[1])
            except:
                continue

    with open(CHEAT_MORPH, 'w') as f:
        for key, value in existing_parses.items():
            print("{}\t{}".format(key, '\t'.join(value)), file=f)
