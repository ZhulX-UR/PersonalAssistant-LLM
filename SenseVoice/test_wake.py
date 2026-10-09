import unittest

from wake import ConversationGate, parse_aliases


class ConversationGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = ConversationGate("爱莉", parse_aliases("爱丽，艾莉,艾丽"), 30)

    def test_wake_corrects_alias_and_accepts_followup(self):
        self.assertEqual(self.gate.process("今天天气怎么样", now=100).event, "ignored")
        self.assertEqual(self.gate.process("爱丽，今天天气怎么样？", now=101).text, "爱莉，今天天气怎么样？")
        self.assertEqual(self.gate.process("接着说", now=125).event, "accepted")
        self.assertEqual(self.gate.remaining(now=154), 1)
        self.assertEqual(self.gate.process("再说一句", now=155).event, "ignored")

    def test_name_alone_wakes_and_expires(self):
        self.assertEqual(self.gate.process("艾莉！", now=10).event, "woke")
        self.assertEqual(self.gate.process("帮我记一下", now=39).event, "accepted")
        self.assertEqual(self.gate.remaining(now=69), 0)
        self.assertEqual(self.gate.process("帮我记一下", now=70).event, "ignored")

    def test_does_not_wake_for_substrings_or_alice(self):
        for phrase in ("我喜欢爱丽", "爱丽丝在这里", "今天很安静"):
            self.assertEqual(self.gate.process(phrase, now=10).event, "ignored")

    def test_alias_settings_are_explicit(self):
        self.assertEqual(parse_aliases("爱丽，艾莉;爱丽\n艾丽"), ("爱丽", "艾莉", "艾丽"))
        self.assertEqual(self.gate.process("艾力", now=10).event, "ignored")


if __name__ == "__main__":
    unittest.main()
