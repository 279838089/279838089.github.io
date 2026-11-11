import unittest
from render import choose_form
class FormTest(unittest.TestCase):
    def test_hours(self):
        for hour,name in [(0,"mega_y"),(5,"mega_y"),(6,"normal"),(11,"normal"),(12,"mega_x"),(17,"mega_x"),(18,"mega_y"),(23,"mega_y")]:
            self.assertEqual(choose_form(hour)[0],name)
if __name__ == "__main__": unittest.main()
