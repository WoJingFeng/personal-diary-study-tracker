import os
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_

from extensions import db, login_manager
from models import Diary, StudyLog, User


load_dotenv()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_path = os.path.join(app.instance_path, "app.db")
        database_url = f"sqlite:///{database_path}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "请先登录后再继续。"

    register_template_filters(app)
    register_routes(app)

    with app.app_context():
        db.create_all()
        ensure_default_user()

    return app


def ensure_default_user():
    username = os.getenv("APP_USERNAME", "admin").strip() or "admin"
    password = os.getenv("APP_PASSWORD", "change-me")

    if User.query.filter_by(username=username).first():
        return

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()


def register_template_filters(app):
    @app.template_filter("minutes_label")
    def minutes_label(minutes):
        minutes = int(minutes or 0)
        hours = minutes // 60
        remaining = minutes % 60
        if hours and remaining:
            return f"{hours} 小时 {remaining} 分钟"
        if hours:
            return f"{hours} 小时"
        return f"{remaining} 分钟"


def parse_date(value, fallback=None):
    if not value:
        return fallback or date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_int(value, default=0, minimum=None, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default

    if minimum is not None:
        number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)
    return number


def normalize_tags(raw_tags):
    tags = []
    for item in (raw_tags or "").replace(",", " ").split():
        tag = item.strip()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = f"#{tag}"
        tags.append(tag)
    return " ".join(dict.fromkeys(tags))


def current_owner():
    return current_user if current_user.is_authenticated else None


def apply_date_filters(query, model):
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if start_date:
        query = query.filter(model.entry_date >= parse_date(start_date))
    if end_date:
        query = query.filter(model.entry_date <= parse_date(end_date))
    return query


def dashboard_stats():
    today = date.today()
    start_day = today - timedelta(days=6)

    diary_count_7d = (
        Diary.query.filter(Diary.user_id == current_user.id)
        .filter(Diary.entry_date >= start_day, Diary.entry_date <= today)
        .count()
    )

    total_study_minutes = (
        db.session.query(func.coalesce(func.sum(StudyLog.minutes), 0))
        .filter(StudyLog.user_id == current_user.id)
        .scalar()
    )

    completed_count = (
        StudyLog.query.filter(StudyLog.user_id == current_user.id)
        .filter(StudyLog.is_completed.is_(True))
        .count()
    )

    chart_labels = []
    chart_values = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        minutes = (
            db.session.query(func.coalesce(func.sum(StudyLog.minutes), 0))
            .filter(StudyLog.user_id == current_user.id)
            .filter(StudyLog.entry_date == day)
            .scalar()
        )
        chart_labels.append(day.strftime("%m/%d"))
        chart_values.append(int(minutes or 0))

    return {
        "diary_count_7d": diary_count_7d,
        "total_study_minutes": int(total_study_minutes or 0),
        "completed_count": completed_count,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    }


def register_routes(app):
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash("登录成功。", "success")
                next_url = request.args.get("next")
                return redirect(next_url or url_for("index"))

            flash("用户名或密码不正确。", "error")

        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("已退出登录。", "success")
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def index():
        stats = dashboard_stats()
        recent_diaries = (
            Diary.query.filter_by(user_id=current_user.id)
            .order_by(Diary.entry_date.desc(), Diary.updated_at.desc())
            .limit(5)
            .all()
        )
        recent_study_logs = (
            StudyLog.query.filter_by(user_id=current_user.id)
            .order_by(StudyLog.entry_date.desc(), StudyLog.updated_at.desc())
            .limit(5)
            .all()
        )
        return render_template(
            "index.html",
            recent_diaries=recent_diaries,
            recent_study_logs=recent_study_logs,
            **stats,
        )

    @app.route("/diaries")
    @login_required
    def diaries():
        q = request.args.get("q", "").strip()
        tag = request.args.get("tag", "").strip()

        query = Diary.query.filter_by(user_id=current_user.id)

        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    Diary.title.ilike(like),
                    Diary.body.ilike(like),
                    Diary.mood_tags.ilike(like),
                )
            )

        if tag:
            normalized = tag if tag.startswith("#") else f"#{tag}"
            query = query.filter(Diary.mood_tags.ilike(f"%{normalized}%"))

        query = apply_date_filters(query, Diary)
        items = query.order_by(Diary.entry_date.desc(), Diary.updated_at.desc()).all()

        return render_template("diaries.html", diaries=items)

    @app.route("/diaries/new", methods=["GET", "POST"])
    @login_required
    def new_diary():
        if request.method == "POST":
            diary = Diary(user_id=current_user.id)
            save_diary_from_form(diary)
            db.session.add(diary)
            db.session.commit()
            flash("日记已保存。", "success")
            return redirect(url_for("diaries"))

        diary = Diary(entry_date=date.today(), title="", body="", mood_tags="")
        return render_template("diary_form.html", diary=diary, mode="new")

    @app.route("/diaries/<int:diary_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_diary(diary_id):
        diary = Diary.query.filter_by(id=diary_id, user_id=current_user.id).first_or_404()

        if request.method == "POST":
            save_diary_from_form(diary)
            db.session.commit()
            flash("日记已更新。", "success")
            return redirect(url_for("diaries"))

        return render_template("diary_form.html", diary=diary, mode="edit")

    @app.route("/diaries/<int:diary_id>/delete", methods=["POST"])
    @login_required
    def delete_diary(diary_id):
        diary = Diary.query.filter_by(id=diary_id, user_id=current_user.id).first_or_404()
        db.session.delete(diary)
        db.session.commit()
        flash("日记已删除。", "success")
        return redirect(url_for("diaries"))

    @app.route("/study")
    @login_required
    def study_logs():
        q = request.args.get("q", "").strip()
        subject = request.args.get("subject", "").strip()

        query = StudyLog.query.filter_by(user_id=current_user.id)

        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    StudyLog.subject.ilike(like),
                    StudyLog.summary.ilike(like),
                )
            )

        if subject:
            query = query.filter(StudyLog.subject.ilike(f"%{subject}%"))

        query = apply_date_filters(query, StudyLog)
        items = query.order_by(StudyLog.entry_date.desc(), StudyLog.updated_at.desc()).all()

        return render_template("study_logs.html", study_logs=items)

    @app.route("/study/new", methods=["GET", "POST"])
    @login_required
    def new_study_log():
        if request.method == "POST":
            study_log = StudyLog(user_id=current_user.id)
            save_study_log_from_form(study_log)
            db.session.add(study_log)
            db.session.commit()
            flash("学习记录已保存。", "success")
            return redirect(url_for("study_logs"))

        study_log = StudyLog(
            entry_date=date.today(),
            subject="",
            minutes=30,
            summary="",
            completion_percent=100,
            is_completed=False,
        )
        return render_template("study_form.html", study_log=study_log, mode="new")

    @app.route("/study/<int:log_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_study_log(log_id):
        study_log = StudyLog.query.filter_by(id=log_id, user_id=current_user.id).first_or_404()

        if request.method == "POST":
            save_study_log_from_form(study_log)
            db.session.commit()
            flash("学习记录已更新。", "success")
            return redirect(url_for("study_logs"))

        return render_template("study_form.html", study_log=study_log, mode="edit")

    @app.route("/study/<int:log_id>/delete", methods=["POST"])
    @login_required
    def delete_study_log(log_id):
        study_log = StudyLog.query.filter_by(id=log_id, user_id=current_user.id).first_or_404()
        db.session.delete(study_log)
        db.session.commit()
        flash("学习记录已删除。", "success")
        return redirect(url_for("study_logs"))

    @app.route("/search")
    @login_required
    def search():
        q = request.args.get("q", "").strip()
        diary_results = []
        study_results = []

        if q:
            like = f"%{q}%"
            diary_results = (
                Diary.query.filter_by(user_id=current_user.id)
                .filter(
                    or_(
                        Diary.title.ilike(like),
                        Diary.body.ilike(like),
                        Diary.mood_tags.ilike(like),
                    )
                )
                .order_by(Diary.entry_date.desc())
                .all()
            )
            study_results = (
                StudyLog.query.filter_by(user_id=current_user.id)
                .filter(or_(StudyLog.subject.ilike(like), StudyLog.summary.ilike(like)))
                .order_by(StudyLog.entry_date.desc())
                .all()
            )

        return render_template(
            "search.html",
            q=q,
            diary_results=diary_results,
            study_results=study_results,
        )


def save_diary_from_form(diary):
    diary.entry_date = parse_date(request.form.get("entry_date"))
    diary.title = request.form.get("title", "").strip() or "无标题"
    diary.body = request.form.get("body", "").strip()
    diary.mood_tags = normalize_tags(request.form.get("mood_tags", ""))


def save_study_log_from_form(study_log):
    study_log.entry_date = parse_date(request.form.get("entry_date"))
    study_log.subject = request.form.get("subject", "").strip() or "未分类"
    study_log.minutes = parse_int(request.form.get("minutes"), default=0, minimum=0)
    study_log.summary = request.form.get("summary", "").strip()
    study_log.completion_percent = parse_int(
        request.form.get("completion_percent"),
        default=100,
        minimum=0,
        maximum=100,
    )
    study_log.is_completed = request.form.get("is_completed") == "on"


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
