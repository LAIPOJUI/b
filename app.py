from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///journal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-secret"  # 用於 flash 訊息

db = SQLAlchemy(app)

# 資料模型：標題、日期、內容
class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<JournalEntry {self.id} {self.title!r}>"


@app.before_request
def ensure_db():
    # 第一次啟動時建立資料表
    with app.app_context():
        db.create_all()


# 首頁：文章列表
@app.route("/")
def index():
    entries = JournalEntry.query.order_by(desc(JournalEntry.date), desc(JournalEntry.id)).all()
    return render_template("index.html", entries=entries)


# 新增文章（表單）
@app.route("/entry/new", methods=["GET", "POST"])
def create_entry():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        date_str = request.form.get("date", "")
        content = request.form.get("content", "").strip()

        if not title or not date_str or not content:
            flash("標題、日期、內容都是必填的喔！", "error")
            return render_template("create.html", title=title, date=date_str, content=content)

        try:
            entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("日期格式不正確，請用 YYYY-MM-DD。", "error")
            return render_template("create.html", title=title, date=date_str, content=content)

        entry = JournalEntry(title=title, date=entry_date, content=content)
        db.session.add(entry)
        db.session.commit()
        flash("已新增日誌文章！", "success")
        return redirect(url_for("index"))

    # GET
    return render_template("create.html", date=date.today().strftime("%Y-%m-%d"))


# 顯示單篇
@app.route("/entry/<int:entry_id>")
def show_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    return render_template("show.html", entry=entry)


# 編輯
@app.route("/entry/<int:entry_id>/edit", methods=["GET", "POST"])
def edit_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        date_str = request.form.get("date", "")
        content = request.form.get("content", "").strip()

        if not title or not date_str or not content:
            flash("標題、日期、內容都是必填的喔！", "error")
            return render_template("edit.html", entry=entry)

        try:
            entry.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("日期格式不正確，請用 YYYY-MM-DD。", "error")
            return render_template("edit.html", entry=entry)

        entry.title = title
        entry.content = content
        db.session.commit()
        flash("已更新日誌文章！", "success")
        return redirect(url_for("show_entry", entry_id=entry.id))

    # GET
    return render_template("edit.html", entry=entry)


# 刪除
@app.route("/entry/<int:entry_id>/delete", methods=["POST"])
def delete_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash("已刪除日誌文章。", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
