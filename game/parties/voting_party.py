from collections import Counter
from functools import reduce

import text_templates
from game.parties import Party


class VotingParty(Party):
    def __init__(self, interface, channel_name, welcome_text_label, before_voting_label, result_text_label, list_label):
        # FIXME:
        # pylint: disable=too-many-arguments
        super().__init__(interface, channel_name, welcome_text_label)
        self.before_voting_label = before_voting_label
        self.result_text_label = result_text_label
        self.list_label = list_label

        self.vote_dict = {}

    def reset_state(self):
        super().reset_state()
        self.vote_dict = {}

    async def do_new_voting_phase(self, embed_data):
        print("party do_new_voting_phase")
        await self.interface.send_action_text_to_channel(self.before_voting_label, self.channel_name)
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)

    def get_result_text(self, author_id, target_id):
        print("party get_result_text")
        return text_templates.generate_text(self.result_text_label, author=f"<@{author_id}>", target=f"<@{target_id}>")

    def do_end_voting_phase(self):
        self.vote_dict = {}

    def register_vote(self, author_id, target_id, vote_weight=1):
        print(f"register vote: {author_id} -> {target_id} x{vote_weight}")
        self.vote_dict[author_id] = (target_id, vote_weight)
        return self.get_result_text(author_id, target_id)

    def get_top_voted(self):
        # FIXME
        # pylint: disable=duplicate-code
        list_id = self.__parse_vote_dict()
        top_voted = Counter(list_id).most_common(2)
        print("get_top_voted", top_voted)
        if len(top_voted) == 1 or (len(top_voted) == 2 and top_voted[0][1] > top_voted[1][1]):
            return top_voted[0][0], top_voted[0][1]
        return None, 0  # have no vote or equal voted

    def __parse_vote_dict(self):
        voted_list = []
        for voted, vote_weight in self.vote_dict.values():
            voted_list += [voted] * vote_weight
        return voted_list

    def get_vote_status(self):
        # From {"u1": ("u2", 1), "u2": ("u1", 1), "u3": ("u1", 1)}
        # to {"u2": {"u1"}, "u1": {"u3", "u2"}}
        table_dict = reduce(lambda d, kv: d.setdefault(kv[1][0], set()).add(kv[0]) or d, self.vote_dict.items(), {})
        print(table_dict)
        return table_dict

    def get_vote_table_with_title(self):
        vote_table = {f'<@{k}>': v for k, v in self.get_vote_status().items()}
        table_title = text_templates.get_label_in_language(self.list_label)
        return vote_table, table_title
