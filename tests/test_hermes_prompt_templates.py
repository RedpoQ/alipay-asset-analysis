import unittest

from asset_analysis.hermes.prompt_templates import (
    CRONJOB_TEMPLATE_PATH,
    FAILURE_PROMPT_PATH,
    README_TEMPLATE_PATH,
    SUCCESS_PROMPT_PATH,
    load_prompt_template,
)


class HermesPromptTemplatesTests(unittest.TestCase):
    def test_prompt_template_contains_do_not_override_signals(self):
        text = load_prompt_template("success").lower()
        self.assertIn("do not override signals", text)

    def test_prompt_template_contains_do_not_predict(self):
        text = load_prompt_template("success").lower()
        self.assertIn("do not predict", text)

    def test_cronjob_yaml_template_exists_and_includes_schedule(self):
        self.assertTrue(CRONJOB_TEMPLATE_PATH.exists())
        content = CRONJOB_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertIn("schedule:", content)

    def test_required_prompt_and_readme_files_exist(self):
        self.assertTrue(SUCCESS_PROMPT_PATH.exists())
        self.assertTrue(FAILURE_PROMPT_PATH.exists())
        self.assertTrue(README_TEMPLATE_PATH.exists())


if __name__ == "__main__":
    unittest.main()
