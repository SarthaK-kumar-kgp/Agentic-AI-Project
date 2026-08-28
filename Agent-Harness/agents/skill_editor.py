from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / "skills"
SKILLS_INDEX = SKILLS_DIR / "README.md"


class SkillEditor:
    def __init__(self, skills_dir=SKILLS_DIR):
        self.skills_dir = Path(skills_dir)
        self.skills_index = self.skills_dir / "README.md"

    def apply_decision(self, decision):
        action = decision["action"]

        if action == "do_nothing":
            return {
                "action": action,
                "changed": False,
                "message": "No skill changes needed.",
            }

        if action == "create_new_skill":
            return self.create_or_update_skill(decision, action)

        if action == "update_existing_skill":
            return self.create_or_update_skill(decision, action)

        return {
            "action": action,
            "changed": False,
            "message": "Unknown skill editor action.",
        }

    def create_or_update_skill(self, decision, action):
        skill_path = decision["skill_path"]
        skill_markdown = decision["proposed_skill_markdown"]
        readme_entry = decision["proposed_readme_entry"]

        if not self.is_safe_skill_path(skill_path):
            return {
                "action": action,
                "changed": False,
                "message": "Unsafe skill path.",
            }

        skill_file = self.skills_dir / skill_path
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(skill_markdown)

        readme_changed = self.update_skills_index(readme_entry)

        return {
            "action": action,
            "changed": True,
            "skill_path": skill_path,
            "readme_changed": readme_changed,
        }

    def update_skills_index(self, readme_entry):
        if readme_entry is None:
            return False

        current_text = self.skills_index.read_text()

        if "No skills available yet." in current_text:
            updated_text = current_text.replace("No skills available yet.", readme_entry)
        else:
            if readme_entry in current_text:
                return False
            updated_text = current_text + "\n\n" + readme_entry + "\n"

        self.skills_index.write_text(updated_text)
        return True

    def is_safe_skill_path(self, skill_path):
        if skill_path is None:
            return False

        if skill_path.startswith("/"):
            return False

        if ".." in skill_path:
            return False

        if not skill_path.endswith("SKILL.md"):
            return False

        return True
