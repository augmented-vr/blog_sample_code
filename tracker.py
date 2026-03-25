import tkinter as tk # GUI(画面) を作るための標準ライブラリ
from tkinter import messagebox # ポップアップメッセージ(警告や確認)を出すためのモジュール
import csv # CSVファイルを読み書きするためのモジュール
import os # ファイルの存在確認など、OS(パソコン)の機能を使うためのモジュール

# このコードが置かれているフォルダの絶対パスを取得する
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 取得した絶対パスとファイル名を結合して、保存先を指定する
CSV_FILE = os.path.join(BASE_DIR, "tcg_records.csv")

class DuelTracker:
    # __init__ はこのアプリが起動した時に最初に呼ばれる「初期設定」の関数
    def __init__(self, master):
        # 1.操作パネル(メインウィンドウ)の設定
        self.master = master
        self.master.title("操作パネル(自分用)") # ウィンドウの上に表示されるタイトル
        self.master.geometry("420x580") # ウィンドウのサイズ
        self.master.attributes("-topmost", True) # 操作パネルを常に最前面に表示する

        # 記録を一時的に保存するための空のリスト(配列)を用意
        self.records = []
        # アプリ起動時に、過去のCSVファイルがあれば読み込む
        self.load_csv()

        # 2.配信画面用ウィンドウ(OBSキャプチャ用)の設定
        # Toplevel()を使うと、メインウィンドウとは別の新しいウィンドウを作れる
        self.disp_win = tk.Toplevel(self.master)
        self.disp_win.title("配信画面用(OBS)")
        self.disp_win.geometry("1100x150")
        self.disp_win.configure(bg="#00FF00") # 背景色を緑色(グリーンバック)に設定

        # OBS用ウィンドウの中に、要素を並べるための透明な「枠(フレーム)」を2つ作る
        # pady=(上, 下)で、フレームの外側に隙間(余白)を作る
        frame_line1 = tk.Frame(self.disp_win, bg="#00FF00")
        frame_line1.pack(pady=(10, 5))

        frame_line2 = tk.Frame(self.disp_win, bg="#00FF00")
        frame_line2.pack(pady=(0, 10))

        # 1行目のラベル(文字を表示する部品)を配置
        # bg:背景色, fg:文字色(フォントカラー)
        self.lbl_theme = tk.Label(frame_line1, text="テーマ: -", font=("Helvetica", 24, "bold"), bg="#00FF00", fg="white")
        # side=tk.LEFT で左から順番に詰めて配置、padx=15 で左右に15ピクセルの隙間を作る
        self.lbl_theme.pack(side=tk.LEFT, padx=15)

        self.lbl_total = tk.Label(frame_line1, text="試合数: 0", font=("Helvetica", 24, "bold"), bg="#00FF00", fg="white")
        self.lbl_total.pack(side=tk.LEFT, padx=15)

        self.lbl_win = tk.Label(frame_line1, text="0勝 0敗 (勝率 0.0%)", font=("Helvetica", 28, "bold"), bg="#00FF00", fg="yellow")
        self.lbl_win.pack(side=tk.LEFT, padx=15)

        # 2行目のラベルを配置
        self.lbl_coin = tk.Label(frame_line2, text="コイン表: 0回(0.0%) / 先攻: 0回(0.0%)", font=("Helvetica", 24, "bold"), bg="#00FF00", fg="white")
        self.lbl_coin.pack(side=tk.LEFT, padx=15)

        # 3.操作パネル(メイン画面)の部品を配置
        # デッキテーマ入力欄
        tk.Label(self.master, text="1. デッキテーマ:").pack(pady=(10, 0))
        # tk.StringVar() は、入力欄の文字をプログラムで取得・変更できるようにするための特殊な変数
        self.theme_var = tk.StringVar(value="マイデッキ")
        tk.Entry(self.master, textvariable=self.theme_var, font=("Helvetica", 12)).pack()

        # command= には、ボタンが押された時に実行したい関数名(()はつけない)を指定する
        tk.Button(self.master, text="テーマを切り替えて過去の戦績を読み込む", command=self.reload_data, bg="#ddddff").pack(pady=5)

        # コイントスのラジオボタン (どれか1つしか選べないボタン)
        tk.Label(self.master, text="2. コイントス結果:").pack(pady=(10,0))
        self.coin_var = tk.StringVar(value="表")
        frame_coin = tk.Frame(self.master)
        frame_coin.pack()
        # variable に同じ変数を指定することでグループ化される
        tk.Radiobutton(frame_coin, text="表", variable=self.coin_var, value="表", font=("Helvetica", 12)).pack(side=tk.LEFT)
        tk.Radiobutton(frame_coin, text="裏", variable=self.coin_var, value="裏", font=("Helvetica", 12)).pack(side=tk.LEFT)

        # 先攻、後攻のラジオボタン
        tk.Label(self.master, text="3. ターン:").pack(pady=(5, 0))
        self.turn_var = tk.StringVar(value="先攻")
        frame_turn = tk.Frame(self.master)
        frame_turn.pack()
        tk.Radiobutton(frame_turn, text="先攻", variable=self.turn_var, value="先攻", font=("Helvetica", 12)).pack(side=tk.LEFT)
        tk.Radiobutton(frame_turn, text="後攻", variable=self.turn_var, value="後攻", font=("Helvetica", 12)).pack(side=tk.LEFT)

        # 勝敗記録ボタン
        tk.Label(self.master, text="4. 試合終了時にクリックして記録保存:").pack(pady=(15, 0))
        frame_res = tk.Frame(self.master)
        frame_res.pack()

        # 単に command=self.add_record("勝利")と書くと、ボタンを表示した瞬間に実行されてしまうため、
        # lambdaを使って「クリックされた時に初めて、引数付きでadd_recordを実行する」という動きにする
        tk.Button(frame_res, text="勝利", width=8, height=2, font=("Helvetica", 12, "bold"), bg="#aaffaa", command=lambda: self.add_record("勝利")).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_res, text="敗北", width=8, height=2, font=("Helvetica", 12, "bold"), bg="#ffaaaa", command=lambda: self.add_record("敗北")).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_res, text="引分", width=8, height=2, font=("Helvetica", 12, "bold"), bg="#cccccc", command=lambda: self.add_record("引き分け")).pack(side=tk.LEFT, padx=5)

        # その他の機能ボタン
        tk.Button(self.master, text="< 現在のテーマの1つ前の記録を取り消す", command=self.undo).pack(pady=(20, 5))
        tk.Button(self.master, text="| 現在のテーマの記録を全てリセット", command=self.reset_theme, bg="#ffdddd").pack(pady=5)
        tk.Button(self.master, text="! 全テーマの記録を全てリセット", command=self.reset_all, bg="#ff9999").pack(pady=5)
        tk.Button(self.master, text="? 全テーマの合計戦績を確認(自分のみ表示)", command=self.show_total_stats, bg="#e0ffff").pack(pady=(15, 5))

        # アプリ起動時に、一旦画面の表示を最新状態に更新する
        self.update_display()

    # ===========================    
    # データ処理を行うための関数群
    # ===========================

    def load_csv(self):
        # CSVファイルから過去のデータを読み込む処理
        # ファイルが存在するかどうかをチェック(初回起動時はファイルが無いのでエラーを防ぐ)
        if os.path.exists(CSV_FILE):
            # "utf-8-sig" は日本語の文字化けを防ぐための文字コード指定
            with open(CSV_FILE, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f) #ヘッダー(1行目)をキーにして辞書型として読み込む
                for row in reader:
                    # strip() は、文字の前後にある不要なスペース(空白)を削除する機能
                    row['theme'] = row.get('theme', '').strip()

                    # 過去のテストなどで混ざった不要なデータ(空欄など)を無視し、正しい結果のみをリストに追加する
                    if row.get('result') in ["勝利", "敗北", "引き分け"]:
                        self.records.append(row)

    def save_csv(self):
        # 現在のself.recordsの中身をCSVファイルに上書き保存する処理
        with open(CSV_FILE, mode="w", encoding="utf-8-sig", newline="") as f:
            fieldnames = ["theme", "coin", "turn", "result"] # CSVの列(ヘッダー)の並び順
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader() # 1行目にヘッダーを書き込む
            writer.writerows(self.records) # リストの中身を一気に書き込む

    def reload_data(self):
        #CSVからデータを読み込み直して画面をリフレッシュする処理
        self.records = [] # 現在メモリに乗っているデータをいったん空にする
        self.load_csv() # csvから最新のデータを読み直す
        self.update_display()

    def add_record(self, result):
        # 勝敗ボタンが押された時、現在の状態を記録する処理
        # 現在画面で選ばれている状態をひとまとめのデータ(辞書型)にする
        record = {
            "theme": self.theme_var.get().strip(),
            "coin": self.coin_var.get(),
            "turn": self.turn_var.get(),
            "result": result
        }
        self.records.append(record) # リストの末尾にデータを追加
        self.save_csv() # 変更をCSVに保存
        self.update_display() # 画面の表示を更新

    def undo(self):
        # 現在のテーマの最後の記録を取り消す処理
        current_theme = self.theme_var.get().strip()
        # reversed() を使って、リストの後ろ(最新の記録)から逆順に探していく
        for i in reversed(range(len(self.records))):
            if self.records[i]['theme'] == current_theme:
                del self.records[i] # 条件に合った記録を1つだけ削除する
                self.save_csv()
                self.update_display()
                break # 1つ消したらループを強制終了(2つ以上消えないようにするため)

    def reset_theme(self):
        # 現在のテーマの記録を全消去する処理
        current_theme = self.theme_var.get().strip()
        # askyesno で「はい(True)」「いいえ(False)」を選択させるダイアログを表示(\n は改行の意味)
        ans = messagebox.askyesno("リセットの確認", f"テーマ「{current_theme}」の戦績をすべて削除してもよろしいですか?\n (※この操作は元に戻せません)")


        if ans: # ans が True(はい)の時だけ実行
            # [内包表記]「テーマが現在入力されているものと『違う(!=)』データだけを残して、新しいリストを作る」という意味
            self.records = [r for r in self.records if r['theme'] != current_theme]
            self.save_csv()
            self.update_display()

    def reset_all(self):
        # 全ての記録を全消去する処理
        ans = messagebox.askyesno("全リセットの確認", "【警告】すべてのテーマの戦績を完全に削除してもよろしいですか?\n (※この操作は元に戻せません)")

        if ans:
            self.records = [] # リストの中身を空っぽにする
            self.save_csv()
            self.update_display()

    def show_total_stats(self):
        # 全テーマの合計戦績を計算し、ポップアップで自分だけに表示する機能
        # theme_records に絞り込まず、self.records(全データ)を対象に計算する
        # sum(1 for ...) は、「条件に合うものがあったら1を足していく」というテクニック
        wins = sum(1 for r in self.records if r['result'] == "勝利")
        losses = sum(1 for r in self.records if r['result'] == "敗北")
        draws = sum(1 for r in self.records if r['result'] == "引き分け")

        total = wins + losses + draws

        # 記録が1つもない場合の処理
        if total == 0:
            messagebox.showinfo("全テーマ合計戦績", "まだ記録がありません。")
            return
        
        coin_heads = sum(1 for r in self.records if r['coin'] == "表")
        turn_first = sum(1 for r in self.records if r['turn'] == "先攻")

        heads_rate = (coin_heads / total * 100) if total > 0 else 0.0
        first_rate = (turn_first / total * 100) if total > 0 else 0.0
        win_rate = (wins / total * 100) if total > 0 else 0.0

        # メッセージボックスに表示するテキストを組み立てる
        msg = f"【全テーマ合計戦績】 \n\n"
        msg += f"総試合数: {total}試合\n"
        msg += f"勝敗: {wins}勝 {losses}敗 {draws}分 (勝率 {win_rate:.1f}%)\n\n"
        msg += f"コイン表: {coin_heads}回 ({heads_rate:.1f}%)\n"
        msg += f"先攻取得: {turn_first}回 ({first_rate:.1f}%)"

        # コピーできる画面とボタンを作る
        popup = tk.Toplevel(self.master)
        popup.title("全テーマ合計戦績")
        popup.geometry("350x380")
        popup.attributes("-topmost", True)

        # 文字を選択できるテキストエリア
        # height=12でテキストエリアの最大高さを制限し、ボタンが押し出されないようにする
        text_widget = tk.Text(popup, font=("Helvetica", 12), padx=10, pady=10, height=12)
        text_widget.insert(tk.END, msg)
        text_widget.config(state=tk.DISABLED) #誤って書き換えないようにする
        text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=(10, 0))

        # コピーボタンが押された時の処理
        def copy_text():
            popup.clipboard_clear() # パソコンのクリップボードを一旦空にする
            popup.clipboard_append(msg) # テキストをクリップボードに記憶させる
            messagebox.showinfo("完了", "テキストをコピーしました! \nYouTubeのコメント欄等に貼り付け(Ctrl+V)できます。", parent=popup)

        # ワンクリックでコピーできるボタンを追加
        tk.Button(popup, text= "クリップボードにコピー", command=copy_text, bg="#ddffdd", font=("Helvetica", 12, "bold")).pack(pady=15)

    def update_display(self):
        # 計算を行い、OBS画面用のラベル(文字)を更新する処理
        current_theme = self.theme_var.get().strip()

        # [内包表記] 現在のテーマと一致する記録だけを抽出して新しいリストを作る
        theme_records = [r for r in self.records if r['theme'] == current_theme]

        # それぞれの条件に一致する数をカウントする
        wins = sum(1 for r in theme_records if r['result'] == "勝利")
        losses = sum(1 for r in theme_records if r['result'] == "敗北")
        draws = sum(1 for r in theme_records if r['result'] == "引き分け")

        # 3つの合計を「試合数」とすることで計算のずれを防ぐ
        total = wins + losses + draws

        coin_heads = sum(1 for r in theme_records if r['coin'] == "表")
        turn_first = sum(1 for r in theme_records if r['turn'] == "先攻")

        # パーセンテージの計算。totalが0の時に割り算をするとエラーになるので、
        # totalが0より大きいときだけ計算し、そうでないときは0.0にするという条件分岐にする
        heads_rate = (coin_heads / total * 100) if total > 0 else 0.0
        first_rate = (turn_first / total * 100) if total > 0 else 0.0
        win_rate = (wins / total * 100) if total > 0 else 0.0

        # config()を使って、画面に配置済みのラベルのtext(文字)を書き換える
        self.lbl_theme.config(text=f"テーマ: {current_theme}")
        self.lbl_total.config(text=f"試合数: {total}")

        self.lbl_coin.config(text=f"コイン表: {coin_heads}回({heads_rate:.1f}%) / 先攻: {turn_first}回({first_rate:.1f}%)")

        # 引き分けが1回以上ある場合のみ「分」を表示するように分岐
        if draws > 0:
            self.lbl_win.config(text=f"{wins}勝 {losses}敗 {draws}分 (勝率 {win_rate:.1f}%)")
        else:
            self.lbl_win.config(text=f"{wins}勝 {losses}敗 (勝率 {win_rate:.1f}%)")

# このファイルが直接実行された時だけ、以下のコードを動かす
if __name__ == "__main__":
    root = tk.Tk() # Tkinterの土台となるメインウィンドウを作成
    app = DuelTracker(root) #上で作ったクラスを呼び出してアプリを起動
    root.mainloop() #アプリをループさせ、ボタンクリックなどのイベントを待機し続ける







