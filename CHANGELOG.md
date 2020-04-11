# Change log

## [Ver. 0.2.0](https://github.com/kanglab/DiamondsOnDash/releases/tag/0.2.0) (2019-10-07)

**Implemented enhancements:**

- 閾値の算出方法を「全シグナルの平均値＋標準偏差x係数」から、シグナルごとの「最小値＋（最大値-最小値）/2」に変更しました。
- 羽化のみの判定に対応しました。
- イベント検出方法を2種類から選べるようにしました（極値を使った方法を追加しました）。
- 活動量シグナルのファイルを選択可能にしました。

**Bugfix:**

- シグナルグラフの選択データ点（赤点）が更新されないバグを修正しました。
- データセットを選択するごとにブラックリストを再読み込みするようにしました。

## [Ver. 0.2.1](https://github.com/kanglab/DiamondsOnDash/releases/tag/0.2.1) (2019-11-21)

**Bugfix:**

- データセットフォルダの名前に括弧（[]）が含まれる場合、globがうまく読み取らないので置換処理を加えました。

## [Ver. 0.3.0](https://github.com/kanglab/DiamondsOnDash/releases/tag/0.3.0) (2019-12-25)

**Implemented enhancements:**

- マスク作成用のタブを作成しました。マスクの作成と保存が可能です。
- 推論用スクリプト（inference.py）の追加
- ChangeFinder シグナル作成用スクリプト（make_CF_signals.py）の追加
- ファイルのリネーム（newviewer.py -> sapphire.py）
- 不要ファイルの削除（mask.py、viewer.py）

## [Ver. 0.3.1](https://github.com/kanglab/DiamondsOnDash/releases/tag/0.3.1) (2020-04-08)

**Modification:**

- Update README.
- Add manual_ja.pdf and manual_en.pdf.
- Add directory tree for demo.
