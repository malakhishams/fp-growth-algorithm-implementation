# IMPORT LIBRARIES
import pandas as pd
import math
from collections import defaultdict
from itertools import combinations

# READ DATA
data = pd.read_excel(r"E:\VS Code stuff\Machine Learning Workspace\dm_task\Horizontal_Format.xlsx")

min_support = float(input("input the min support: "))
min_conf = float(input("input the min confidence: "))

rows, columns = data.shape # get rows to calc min_support

min_supp_cnt = math.ceil(round(rows*min_support, 6)) # only 6 places after the decimal point

transactions = [set(i.strip() for i in r.split(',')) for r in data['items']] #remove spaces then split at ,
transactions = list(transactions) # type cast ti be able to loop over it [we cav't loop over a python set]

items_cnt_temp = dict() # to count all items [freq & infreq]

for row in transactions:
    for item in row:
            items_cnt_temp[item] = items_cnt_temp.get(item, 0) + 1

freq_items_l1 = {} #each itme : its support for the frequent items

for k,v in items_cnt_temp.items():
    if v >= min_supp_cnt:
        freq_items_l1[k] = v

sorted_dict = dict(sorted(freq_items_l1.items(),key=lambda d : d[1],reverse=True))
order={}
i=0
for x in sorted_dict :
    order[x]=i
    i=i+1

filtered=[]
# sort to build the tree
for row in transactions:
    frow=[item for item in row if item in freq_items_l1]
    frow.sort(key=lambda x:order[x])
    filtered.append(frow)


class Node:
    def __init__(self, item, count=1):
        self.item = item # item name
        self.count = count # item count
        self.children = {} # all children nodes
        self.parent = None # node parent
        self.node_link = None  # link nodes contaning the same item

root = Node("root", 0)


def insert_transaction(root, transaction):

    current = root # must start with the root

    for item in transaction: # insert each item in the transaction

        if item in current.children:
            current.children[item].count += 1 # if the path exists, only increment the node count

        else: # not exist, create new node
            new_node = Node(item)
            new_node.parent = current
            current.children[item] =new_node

        current = current.children[item]  # move 1 level deeper


for t in filtered:
    insert_transaction(root, t)


def traverse(first,level=0):

    print("    " * level + f"{first.item} : {first.count}")
    for n in first.children.values():

        traverse(n,level+1)


traverse(root)


def dfs(node, path):
    if node.parent is not None and node.parent.item != "root":
        path.append(node.parent.item)
        dfs(node.parent, path)


def find_path(item, header_table):
    paths = []
    curr = header_table[item][1]
    while curr is not None:
        path = []
        dfs(curr, path)
        if path:
            paths.append((path, curr.count))
        curr = curr.node_link
    return paths


def group_nodes(node, groups):
    if node is None: return
    if node.item != "root":
        groups[node.item].append(node)
    for ch in node.children.values():
        group_nodes(ch, groups)


def build_header(root, freq):
    groups = defaultdict(list)
    group_nodes(root, groups)

    header = {}
    for item in freq:
        nodes = groups[item]
        for i in range(len(nodes) - 1):
            nodes[i].node_link = nodes[i + 1]
        header[item] = [freq[item], nodes[0]]

    return header


def build_tree(paths, min_sup):
    counts = {}
    for path, weight in paths:
        for it in path:
            counts[it] = counts.get(it, 0) + weight

    freq = {k: v for k, v in counts.items() if v >= min_sup}
    if not freq:
        return None, None

    ordered = sorted(freq.keys(), key=lambda k: (freq[k], k), reverse=True)
    rank = {}
    i = 0
    for it in ordered:
        rank[it] = i
        i += 1

    _root = Node("root", 0)

    for path, weight in paths:
        ordered_path = sorted([it for it in path if it in rank], key=lambda it: rank[it])
        curr = _root
        for it in ordered_path:
            if it in curr.children:
                curr.children[it].count += weight
            else:
                new_node = Node(it, count=weight)
                new_node.parent = curr
                curr.children[it] = new_node
            curr = curr.children[it]

    header = build_header(_root, freq)
    return _root, header


def create_freq_sets(header, minsupport, suff, result):
    for item in sorted(header, key=lambda x: header[x][0]):
        nset = suff | {item}
        result[frozenset(nset)] = header[item][0]
        paths = find_path(item, header)
        _, cond_header = build_tree(paths, minsupport)
        if cond_header:
            create_freq_sets(cond_header, minsupport, nset, result)


header = build_header(root, freq_items_l1)

result = {}
create_freq_sets(header, min_supp_cnt, frozenset(), result)

##########################################################################

for lvl in range(1, max(len(iset) for iset in result) + 1):
    print(f"L{lvl}:", [(set(iset), cnt) for iset, cnt in result.items() if len(iset) == lvl])

'''
Hey Team, 
Malak is telling u how this line work 
L{k}:", [(set(s), c) for s, c in result.items() if len(s) == k
-> we loop from 1 to max itemset lenght (levels count)
-> at each level, we use if len(s) == k to filter the itemsets of lemght l only (of level k)
-> that itemset is saved in results as a dictionary {key : value} => the ley is the items itself and the valuse is support count
=> we put them in (tuple), theat tuple contains (items, count) for example ({'N'}, 2)
=> and does the same for all itemsets of that level

'''


def generate_rules(frequent_itemsets, min_confidence):

    rules = []

    for itemset in frequent_itemsets.keys(): # keys are the items itself as the values are count

        if len(itemset) < 2:
            continue

        for i in range(1, len(itemset)):

            for antecedent in combinations(itemset, i): # generate all possible combinations of intemst elements with size of i

                antecedent = frozenset(antecedent) # rule : antecedent -> consequent
                consequent = itemset - antecedent

                confidence = (
                    frequent_itemsets[itemset] /
                    frequent_itemsets[antecedent]
                )

                if confidence >= min_confidence:
                    rules.append((antecedent, consequent, confidence))

    return rules

########################################################

def print_final_rules(rules):
    for antecedent, consequent, confidence in rules:
        print(f"{set(antecedent)} -> {set(consequent)}")
        print(f"Confidence: {confidence:.2f}")
        print("----------------")

###############################################################

def calc_lift(rules, frequent_itemsets, total_transactions):

    for antecedent, consequent, confidence in rules:   # rule: antecedent -> consequent

        support_consequent = (frequent_itemsets[consequent] / total_transactions)

        lift = confidence / support_consequent

        print(f"{set(antecedent)} -> {set(consequent)}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Lift: {lift:.2f}")

        if lift > 1:
            print("Positive Association")
        elif lift == 1:
            print("No Association")
        else:
            print("Negative Association")

        print("----------------")


rules = generate_rules(result, min_conf)

#############################################################

print("Association Rules:")
print_final_rules(rules)

############################################################

print("\nAssociation Rules with Lift:")
calc_lift(rules, result, rows)