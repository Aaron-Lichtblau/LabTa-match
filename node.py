import copy

class TaNode:
    ta_group_count = 0
    def __init__(self, ta_num):
        self.ta_num = ta_num
        self.group_number = copy.deepcopy(TaNode.ta_group_count)
        TaNode.ta_group_count += 1
    def __str__(self):
        return "{}({})".format(self.ta_num, self.group_number)
    def __repr__(self):
        return "TaNode({})".format(self.ta_num)

class SlotNode:
    slot_group_count = 0
    def __init__(self, slot_num):
        self.slot_num = slot_num
        self.group_number = copy.deepcopy(SlotNode.slot_group_count)
        SlotNode.slot_group_count += 1
    def __str__(self):
        return "{}({})".format(self.slot_num, self.group_number)
    def __repr__(self):
        return "SlotNode({})".format(self.slot_num)
