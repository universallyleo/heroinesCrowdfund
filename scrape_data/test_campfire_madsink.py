import unittest
from bs4 import BeautifulSoup
import campfire_madsink as madsink
from scraper import ParseError, ProjectNotFinished, parse_project_page
from test_scraper import PROJECT_PAGE

class MadsinkTests(unittest.TestCase):
    def test_reviewed_latest_group_mapping_updates_existing_rows_without_mutation(self):
        self.assertTrue(hasattr(madsink, 'refresh_groups'))
        old = [{'subject': {'member':'Q酸素','group':'MADMED','type':'生誕祭'}}]
        new = madsink.refresh_groups(old)
        self.assertEqual(new[0]['subject']['group'],'神様の言う通り/ちちゃめど')
        self.assertEqual(old[0]['subject']['group'],'MADMED')

    def test_title_variants_and_latest_main_collaboration_groups(self):
        for title, member, group, year in [
            ('【Q酸素生誕祭2026】応援プロジェクト','Q酸素','神様の言う通り/ちちゃめど',2026),
            ('ありすりあ 生誕祭プロジェクト2025','ありすりあ','めっ！/ちちゃめど',2025),
            ('【 今世イ憂³】生誕祭応援プロジェクト2026','今世イ憂³','絶望キネマ',2026),
            ('猿馬虎生誕祭2025応援プロジェクト','猿馬虎','MADOROMI/まっずぷりんす',2025),
            ('【暗空夜生誕祭2026】応援プロジェクト','暗空夜','神様の言う通り/まっずぷりんす',2026),
        ]:
            subject, event_year = madsink.parse_details(title,BeautifulSoup('','html.parser'),'')
            self.assertEqual(subject,{'group':group,'member':member,'type':'生誕祭'})
            self.assertEqual(event_year,year)

    def test_last_live_reads_event_schedule_and_unknown_member_conflicts_fail(self):
        soup = BeautifulSoup('<div class="fr-view"><p>生誕イベント:2026年3月14日に開催決定！</p></div>','html.parser')
        subject, year = madsink.parse_details('【那月邪夢 LAST LIVE】応援プロジェクト',soup,'3月に開催する生誕・卒業公演')
        self.assertEqual(year,2026); self.assertEqual(subject['type'],'生誕・卒業公演')
        self.assertEqual(subject['group'],'MADMED')
        with self.assertRaises(ParseError): madsink.parse_details('新人 生誕祭プロジェクト2026',soup,'')
        with self.assertRaises(ParseError): madsink.parse_details('猿馬虎生誕祭2025応援プロジェクト',soup,'')

    def test_financial_parser_is_shared_and_unfinished_page_is_rejected(self):
        page = PROJECT_PAGE.replace('パラレルサイダー＜リア＞＜笑茉＞合同生誕祭応援プロジェクト','Q酸素 生誕祭プロジェクト2025')
        row = parse_project_page(page,'https://camp-fire.jp/projects/123/view',details_parser=madsink.parse_details)
        self.assertEqual(row['total'],1234); self.assertEqual(row['rest'],12)
        self.assertEqual(row['pricePatrons'],[{'price':1000,'patrons':5},{'price':3000,'patrons':1}])
        with self.assertRaises(ProjectNotFinished):
            parse_project_page(page.replace('募集を終了','募集予定'),'https://camp-fire.jp/projects/123/view',details_parser=madsink.parse_details)

if __name__ == '__main__': unittest.main()
