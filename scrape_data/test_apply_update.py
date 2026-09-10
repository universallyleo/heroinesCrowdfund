import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from apply_update import apply_staged_files, commit_and_push


class ApplyStagedFilesTests(unittest.TestCase):
    def test_database_update_creates_exact_backup_before_copying_candidates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "data.json"
            progress = root / "progress.json"
            output = root / "output"
            backup_root = root / "old"
            original_database = [{"url": "https://camp-fire.jp/projects/1/view"}]
            candidate_database = original_database + [{"url": "https://camp-fire.jp/projects/2/view"}]
            original_progress = {"checkpointUrl": "https://camp-fire.jp/projects/1/view", "pending": {}}
            candidate_progress = {"checkpointUrl": "https://camp-fire.jp/projects/2/view", "pending": {}}

            database.write_text(json.dumps(original_database), encoding="utf-8")
            progress.write_text(json.dumps(original_progress), encoding="utf-8")
            output.mkdir()
            (output / "candidate_database.json").write_text(
                json.dumps(candidate_database), encoding="utf-8"
            )
            (output / "candidate_progress.json").write_text(
                json.dumps(candidate_progress), encoding="utf-8"
            )

            result = apply_staged_files(
                {"databaseChanged": True, "progressChanged": True},
                output,
                database,
                progress,
                backup_root,
                "20260910T120000Z",
                "123",
                "1",
            )

            backup = backup_root / "backup_at_20260910T120000Z_run123_attempt1.json"
            self.assertEqual(json.loads(backup.read_text(encoding="utf-8")), original_database)
            self.assertEqual(json.loads(database.read_text(encoding="utf-8")), candidate_database)
            self.assertEqual(json.loads(progress.read_text(encoding="utf-8")), candidate_progress)
            self.assertEqual(result["backup"], str(backup))

    def test_progress_only_update_does_not_create_database_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "data.json"
            progress = root / "progress.json"
            output = root / "output"
            backup_root = root / "old"
            database.write_text("original", encoding="utf-8")
            progress.write_text("old", encoding="utf-8")
            output.mkdir()
            (output / "candidate_progress.json").write_text("new", encoding="utf-8")

            result = apply_staged_files(
                {"databaseChanged": False, "progressChanged": True},
                output,
                database,
                progress,
                backup_root,
                "20260910T120000Z",
                "123",
                "1",
            )

            self.assertFalse(backup_root.exists())
            self.assertEqual(progress.read_text(encoding="utf-8"), "new")
            self.assertIsNone(result["backup"])

    def test_commit_and_push_updates_main_without_merging_remote_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            remote = root / "remote.git"
            repo = root / "repo"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            subprocess.run(["git", "init", "--initial-branch=main", str(repo)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "test"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)

            database = repo / "src" / "data.json"
            progress = repo / "progress.json"
            backup = repo / "old" / "backup.json"
            database.parent.mkdir(parents=True)
            backup.parent.mkdir(parents=True)
            database.write_text("old", encoding="utf-8")
            progress.write_text("old", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "initial"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(remote)], check=True)
            subprocess.run(["git", "-C", str(repo), "push", "-u", "origin", "main"], check=True, capture_output=True)

            database.write_text("new", encoding="utf-8")
            progress.write_text("new", encoding="utf-8")
            backup.write_text("old", encoding="utf-8")
            commit_sha = commit_and_push(
                repo,
                Path("src/data.json"),
                Path("progress.json"),
                "old/backup.json",
                "data: test update",
            )

            remote_sha = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
                text=True,
            ).strip()
            self.assertEqual(commit_sha, remote_sha)


if __name__ == "__main__":
    unittest.main()
