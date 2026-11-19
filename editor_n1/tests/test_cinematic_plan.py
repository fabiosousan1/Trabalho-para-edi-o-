import unittest
from cinematic_plan import classify, plan


class CinematicPlanTests(unittest.TestCase):
    def test_emotional_classification(self):
        self.assertEqual(classify("Você pode recomeçar hoje"), "esperanca")
        self.assertEqual(classify("Esse erro foi difícil"), "desafio")
        self.assertEqual(classify("Consegui meu resultado"), "conquista")

    def test_plan_preserves_timing(self):
        result = plan([{"start": 1.2, "end": 4.5, "text": "Acredite no seu sonho"}])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["start"], 1.2)
        self.assertEqual(result[0]["end"], 4.5)
        self.assertEqual(result[0]["mood"], "esperança")


if __name__ == "__main__":
    unittest.main()
