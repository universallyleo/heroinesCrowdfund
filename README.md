# アイドル クラファ記録

CAMPFIRE の終了済みプロジェクトを事務所別に閲覧する日本語の静的 SPA です。
`heroines/imaginate` と `MAD’S iNK` に対応しています。サーバーや実行時 API は使いません。

## 開発・検証

```sh
bun install
bun run dev
bun test
bun run check
bun run build
python -m unittest discover -s scrape_data -p 'test_*.py' -v
```

Python の依存関係は `requests` と `beautifulsoup4` です。
GitHub Pages のサブパスを検証するときは `BASE_PATH=/heroinesCrowdfund` を設定してビルドします。

## データの更新

GitHub Actions の **Update scraped crowdfunding data** で `agency` を選択します。
`dry_run` は候補ファイルとレポートの作成のみ、`full_scan` は全掲載ページの探索です。
保存済みプロジェクトの詳細ページは再取得しません。

ローカルでの確認：

```sh
python scrape_data/scraper.py --agency madsink --output-dir /path/to/stage
python scrape_data/apply_update.py --agency madsink --output-dir /path/to/stage
```

前者はステージ作成のみ、後者は選択事務所のファイル適用とバックアップのみです。
Git 操作は `--publish` を指定した場合に限り、変更のない `main` チェックアウトから実行します。
レコードが変わると事務所のデータ更新日時も変わります。確認のみ・進捗のみの更新では変わりません。
ページ下部の「サイト更新」はビルド日時です。時刻は日本時間で表示します。

一部の掲載元・プロジェクトで取得に失敗しても、有効な結果は適用できます。
GitHub の警告・サマリー・レポートで未取得分を確認してください。全処理失敗時は適用しません。

## MAD’S iNK の所属情報

CAMPFIRE がグループを記載しないため、[Jpop Wiki](https://jpop.fandom.com/wiki/MAD%27S_iNK) を参照した
`scrape_data/madsink_members.json` の確認済み対応表を使います。
ユーザー指定により、過去のイベントも **最新の所属** を表示します。形式は既存データと同じ
`メイングループ/コラボグループ` です。`ちちゃめど`・`まっずぷりんす` はコラボグループです。
不明なメンバー・別名は推測せず確認してください。対応表の変更は、次回の有効なステージで保存済み
レコードにも反映されます。対応表だけ変更しても公開データは変わりません。

## 事務所の追加・復旧

`src/lib/data/agencies.json` に登録し、独立した空の JSON 配列、`updatedAt: null` のメタデータ、
掲載元ごとの `checkpointUrl: null` と空の `pending` を持つ進捗ファイルを用意します。
`update-data.yml` の選択肢も更新します。HTML・タイトル・イベント年の互換性を確認し、必要なら
既知の scraper ID に対応するパーサーを追加してください。欠けたファイルを heroines のデータで代用しません。

復旧時は `src/lib/data/old/<agency>/` の同一バックアップ名の JSON と `.metadata.json` を一緒に戻し、
コミットしてビルドします。必要なら同時点の進捗を Git から戻すか全探索で確認してください。
push 後にデプロイが失敗した場合は、データコミットを含む現在の `main` で **Build on change to src** を
再実行します。`checkout-ref` も指定できますが、公開時点で `main` と一致しない古いビルドは拒否します。
再スクレイピングで新規データが見つかることを復旧条件にしないでください。

詳細は [AGENTS.md](AGENTS.md) と
[複数事務所の仕様](docs/specs/2026-09-10-implemented-multiple_agency.md) を参照してください。
