import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from apply_update import apply_staged_files, commit_and_push
from agency_config import read_json
from scraper import run_pipeline
from test_agency_config import setup_repo, write
from test_scraper import NEW_LISTING_PAGE, PROJECT_PAGE

class ApplyStagedFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.agency = setup_repo(self.root)['agencies'][0]
        self.output = self.root / 'stage'
        self.pages = {self.agency['scraper']['discoverySources'][0]['listingUrl']:NEW_LISTING_PAGE,
                      'https://camp-fire.jp/projects/300/view': PROJECT_PAGE}
        self.report = run_pipeline('a', self.root, self.output, fetch_text=self.pages.__getitem__)
        self.originals = {key:(self.root / self.agency[key]).read_bytes() for key in ('databasePath','metadataPath','progressPath')}

    def apply(self, report=None):
        return apply_staged_files(report or self.report, self.output, 'a', self.root, '20261115T120000Z','123','1')

    def test_exact_backups_and_only_selected_agency_changes(self):
        result = self.apply()
        self.assertEqual(Path(result['backup']).read_bytes(),self.originals['databasePath'])
        self.assertEqual(Path(result['metadata_backup']).read_bytes(),self.originals['metadataPath'])
        self.assertEqual(len(read_json(self.root / self.agency['databasePath'])),1)
        self.assertEqual(read_json(self.root / 'src/lib/data/agencies/b/projects.json'),[])
        self.assertIsNotNone(read_json(self.root / self.agency['metadataPath'])['updatedAt'])

    def test_wrong_agency_flags_and_missing_candidates_rejected_without_writes(self):
        for changed in [dict(self.report,agencyId='b'), dict(self.report,databaseChanged=False), dict(self.report,outcome='failed')]:
            with self.assertRaises(ValueError): self.apply(changed)
        (self.output / 'candidate_progress.json').unlink()
        with self.assertRaises((ValueError,FileNotFoundError)): self.apply()
        for key,original in self.originals.items(): self.assertEqual((self.root / self.agency[key]).read_bytes(),original)
        self.assertFalse((self.root / self.agency['backupRoot']).exists())

    def test_stale_source_rejected_and_progress_only_does_not_bump_metadata(self):
        progress = self.root / self.agency['progressPath']; progress.write_text(progress.read_text()+' ',encoding='utf-8')
        with self.assertRaises(ValueError): self.apply()
        progress.write_bytes(self.originals['progressPath'])
        self.apply()
        report = run_pipeline('a',self.root,self.output,fetch_text=self.pages.__getitem__)
        # Already-stored completed row is skipped; open pending retry fails, a valid partial stage.
        self.assertFalse(report['databaseChanged']); self.assertFalse(report['metadataChanged'])
        before = (self.root / self.agency['metadataPath']).read_bytes()
        result = self.apply(report)
        self.assertIsNone(result['backup']); self.assertEqual((self.root / self.agency['metadataPath']).read_bytes(),before)

    def test_local_replacement_failure_rolls_back_all_owned_files(self):
        import os
        real_replace = os.replace; calls = 0
        def fail_once(src,dest):
            nonlocal calls
            calls += 1
            if calls == 2: raise OSError('simulated disk failure')
            return real_replace(src,dest)
        with patch('apply_update.os.replace',side_effect=fail_once):
            with self.assertRaises(OSError): self.apply()
        for key,original in self.originals.items(): self.assertEqual((self.root / self.agency[key]).read_bytes(),original)

    def test_metadata_only_correction_is_public_and_invalid_owner_is_rejected(self):
        # Stage an otherwise semantic no-op with a reviewed metadata correction.
        for name, key in [('database','databasePath'),('progress','progressPath')]:
            (self.output / f'candidate_{name}.json').write_bytes(self.originals[key])
        self.report.update(databaseChanged=False, progressChanged=False, metadataChanged=True)
        result = self.apply()
        self.assertIsNone(result['backup'])
        self.assertEqual(result['changed_paths'], [str(self.root / self.agency['metadataPath'])])

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

            # Another writer advances main. The stale checkout must never force-push.
            other = root / 'other'
            subprocess.run(['git','clone','--branch','main',str(remote),str(other)],check=True,capture_output=True)
            subprocess.run(['git','-C',str(other),'config','user.name','other'],check=True)
            subprocess.run(['git','-C',str(other),'config','user.email','other@example.com'],check=True)
            (other / 'progress.json').write_text('remote advance',encoding='utf-8')
            subprocess.run(['git','-C',str(other),'commit','-am','advance'],check=True,capture_output=True)
            subprocess.run(['git','-C',str(other),'push','origin','main'],check=True,capture_output=True)
            database.write_text('stale local update',encoding='utf-8')
            with self.assertRaises(subprocess.CalledProcessError):
                commit_and_push(repo,Path('src/data.json'),Path('progress.json'),None,'stale')
            latest = subprocess.check_output(['git','--git-dir',str(remote),'rev-parse','refs/heads/main'],text=True).strip()
            self.assertNotEqual(latest,subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip())


if __name__ == "__main__":
    unittest.main()
