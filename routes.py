import json
from collections import defaultdict
from functools import wraps

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from models import repo

main_bp = Blueprint("main", __name__)
BRAND_NAME = "RankBridge PG Entrance Mock Tests and PYQs"


def scaled_duration_minutes(test, exam):
    official_questions = max(exam.get("official_question_count") or len(test.get("questions", [])), 1)
    sample_questions = max(len(test.get("questions", [])), 1)
    scaled_minutes = round((exam["duration_minutes"] * sample_questions) / official_questions)
    return max(10, scaled_minutes)


def normalize(document):
    if not document:
        return None
    if isinstance(document, list):
        return [normalize(item) for item in document]
    item = dict(document)
    if "_id" in item:
        item["id"] = item.pop("_id")
    return item


def current_user():
    user_id = session.get("user_id")
    return normalize(repo.get_user_by_id(user_id)) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please login to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped


def decorate_tests(tests, user):
    exams = {exam["slug"]: normalize(exam) for exam in repo.list_exams()}
    output = []
    for raw in tests:
        test = normalize(raw)
        exam = exams.get(test["exam_slug"], {})
        unlocked = repo.user_has_access(user["id"], test) if user else test.get("is_free")
        test["exam"] = exam
        test["question_count"] = len(test.get("questions", []))
        test["unlocked"] = unlocked
        output.append(test)
    return output


def decorate_plans(plans, user=None):
    access = {}
    if user:
        for exam in repo.list_exams():
            access[exam["slug"]] = repo.summarize_exam_access(user["id"], exam["slug"])
    result = []
    for raw in plans:
        plan = normalize(raw)
        plan["owned"] = False
        if user and plan["exam_slug"] == "all":
            profile = repo.access_profile(user["id"])
            plan["owned"] = {"pyq", "mock"}.issubset(profile["all"])
        elif user and plan["exam_slug"] in access:
            tiers = set(plan["access_tiers"])
            owned_access = access[plan["exam_slug"]]
            plan["owned"] = all(owned_access.get(tier, False) for tier in tiers)
        result.append(plan)
    return result


def build_exam_cards(user=None):
    exams = []
    all_tests = repo.list_tests()
    tests_by_exam = defaultdict(list)
    for test in all_tests:
        tests_by_exam[test["exam_slug"]].append(normalize(test))
    for raw_exam in repo.list_exams():
        exam = normalize(raw_exam)
        exam_tests = tests_by_exam.get(exam["slug"], [])
        exam["free_tests"] = sum(1 for item in exam_tests if item.get("is_free"))
        exam["pyq_count"] = sum(1 for item in exam_tests if item["test_type"] == "pyq")
        exam["mock_count"] = sum(1 for item in exam_tests if item["test_type"] == "mock")
        exam["sample_question_count"] = exam.get("sample_question_count", len(exam_tests[0].get("questions", [])) if exam_tests else 0)
        sample_test = exam_tests[0] if exam_tests else {"questions": []}
        exam["sample_duration_minutes"] = scaled_duration_minutes(sample_test, exam) if exam_tests else exam["duration_minutes"]
        exam["access"] = repo.summarize_exam_access(user["id"], exam["slug"]) if user else {"pyq": False, "mock": False, "complete": False}
        exams.append(exam)
    return exams


def build_attempt_summary(attempt):
    answers = attempt.get("answers", [])
    by_section = defaultdict(lambda: {"total": 0, "correct": 0, "wrong": 0, "unanswered": 0})
    for answer in answers:
        section = answer["section"]
        by_section[section]["total"] += 1
        if answer["status"] == "correct":
            by_section[section]["correct"] += 1
        elif answer["status"] == "wrong":
            by_section[section]["wrong"] += 1
        else:
            by_section[section]["unanswered"] += 1
    return [{"section": name, **stats} for name, stats in by_section.items()]


@main_bp.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "mongo_mode": current_app.config.get("MONGO_ACTIVE_MODE", "mongodb"),
        "whatsapp_href": f"https://wa.me/{current_app.config['WHATSAPP_NUMBER']}?text={current_app.config['WHATSAPP_MESSAGE'].replace(' ', '%20')}",
        "brand_name": BRAND_NAME,
    }


@main_bp.route("/")
def landing():
    exams = build_exam_cards()
    featured_tests = decorate_tests(repo.list_tests()[:8], None)
    featured_plans = decorate_plans(repo.list_plans())[:4]
    return render_template("landing.html", exams=exams, featured_tests=featured_tests, featured_plans=featured_plans)


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        if not all([name, email, password]):
            flash("Name, email, and password are required.", "danger")
            return render_template("register.html")
        if repo.get_user_by_email(email):
            flash("An account already exists for that email.", "warning")
            return render_template("register.html")
        user = normalize(repo.create_user(name, email, password, phone))
        session["user_id"] = user["id"]
        flash("Your account is ready. Start with a free PYQ or mock.", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = normalize(repo.get_user_by_email(email))
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")
        session["user_id"] = user["id"]
        flash("You are now logged in.", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("login.html")


@main_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    exams = build_exam_cards(user)
    attempts = [normalize(item) for item in repo.list_attempts_for_user(user["id"], limit=6)]
    purchases = [normalize(item) for item in repo.list_user_purchases(user["id"])]
    plans = decorate_plans(repo.list_plans(), user)
    unlocked_exams = sum(1 for exam in exams if exam["access"]["pyq"] or exam["access"]["mock"])
    return render_template("dashboard.html", exams=exams, attempts=attempts, purchases=purchases, plans=plans, unlocked_exams=unlocked_exams)


@main_bp.route("/tests")
@login_required
def test_library():
    user = current_user()
    exam_slug = request.args.get("exam", "").strip()
    test_type = request.args.get("type", "").strip()
    tests = decorate_tests(repo.list_tests(exam_slug=exam_slug or None, test_type=test_type or None), user)
    exams = build_exam_cards(user)
    return render_template("quizzes.html", tests=tests, exams=exams, selected_exam=exam_slug, selected_type=test_type)


@main_bp.route("/exam/<slug>")
@login_required
def exam_detail(slug):
    user = current_user()
    exam = normalize(repo.get_exam(slug))
    if not exam:
        return render_template("404.html"), 404
    tests = decorate_tests(repo.list_tests(exam_slug=slug), user)
    plans = decorate_plans(repo.list_plans(slug), user)
    access = repo.summarize_exam_access(user["id"], slug)
    return render_template("payment.html", exam=exam, tests=tests, plans=plans, access=access)


@main_bp.route("/checkout/<plan_slug>", methods=["GET", "POST"])
@login_required
def checkout(plan_slug):
    user = current_user()
    plan = normalize(repo.get_plan(plan_slug))
    if not plan:
        return render_template("404.html"), 404
    if request.method == "POST":
        payment_method = request.form.get("payment_method", "UPI")
        purchase, created = repo.create_purchase(user["id"], plan, payment_method)
        if created:
            flash(f"{plan['title']} unlocked successfully.", "success")
        else:
            flash(f"{plan['title']} is already active on your account.", "info")
        return redirect(url_for("main.dashboard"))
    return render_template("checkout.html", plan=plan)


@main_bp.route("/test/<test_id>")
@login_required
def test_page(test_id):
    user = current_user()
    test = normalize(repo.get_test(test_id=test_id))
    if not test:
        return render_template("404.html"), 404
    if not repo.user_has_access(user["id"], test):
        flash("This paper is locked. Buy the matching pass to continue.", "warning")
        return redirect(url_for("main.exam_detail", slug=test["exam_slug"]))
    exam = normalize(repo.get_exam(test["exam_slug"]))
    adaptive_duration_minutes = scaled_duration_minutes(test, exam)
    return render_template("quiz.html", test=test, exam=exam, adaptive_duration_minutes=adaptive_duration_minutes)


@main_bp.route("/api/test/<test_id>")
@login_required
def test_api(test_id):
    user = current_user()
    test = normalize(repo.get_test(test_id=test_id))
    if not test:
        return jsonify({"error": "test_not_found"}), 404
    if not repo.user_has_access(user["id"], test):
        return jsonify({"error": "locked", "redirect": url_for("main.exam_detail", slug=test["exam_slug"])}), 403
    exam = normalize(repo.get_exam(test["exam_slug"]))
    adaptive_duration_minutes = scaled_duration_minutes(test, exam)
    return jsonify({
        "id": test["id"],
        "title": test["title"],
        "subtitle": test["subtitle"],
        "duration_minutes": test["duration_minutes"],
        "adaptive_duration_minutes": adaptive_duration_minutes,
        "negative_marks": test["negative_marks"],
        "difficulty": test["difficulty"],
        "instructions": test["instructions"],
        "exam": {"slug": exam["slug"], "name": exam["name"], "sections": exam["sections"]},
        "questions": [
            {"question_key": q["question_key"], "text": q["text"], "section": q["section"], "marks": q["marks"], "negative_marks": q["negative_marks"], "options": q["options"]}
            for q in test["questions"]
        ],
    })


@main_bp.route("/submit-test", methods=["POST"])
@login_required
def submit_test():
    user = current_user()
    data = request.get_json(silent=True) or {}
    test = normalize(repo.get_test(test_id=data.get("test_id")))
    if not test:
        return jsonify({"error": "test_not_found"}), 404
    if not repo.user_has_access(user["id"], test):
        return jsonify({"error": "locked"}), 403

    answer_map = {item.get("question_key"): item for item in data.get("answers", [])}
    answers = []
    score = 0
    correct = wrong = unanswered = 0

    for question in test["questions"]:
        submitted = answer_map.get(question["question_key"], {})
        selected_option = submitted.get("selected_option", "")
        is_correct = selected_option == question["correct_option"]
        if not selected_option:
            unanswered += 1
            status = "unanswered"
            delta = 0
        elif is_correct:
            correct += 1
            status = "correct"
            delta = question["marks"]
        else:
            wrong += 1
            status = "wrong"
            delta = -question["negative_marks"]
        score += delta
        answers.append({
            "question_key": question["question_key"],
            "section": question["section"],
            "question_text": question["text"],
            "options": question["options"],
            "selected_option": selected_option,
            "correct_option": question["correct_option"],
            "explanation": question["explanation"],
            "status": status,
            "marks_awarded": delta,
        })

    total_questions = len(test["questions"])
    max_score = sum(question["marks"] for question in test["questions"])
    percentage = round((max(score, 0) / max_score) * 100, 2) if max_score else 0
    accuracy = round((correct / (correct + wrong)) * 100, 2) if (correct + wrong) else 0
    attempt = normalize(repo.create_attempt({
        "user_id": user["id"],
        "user_name": user["name"],
        "exam_slug": test["exam_slug"],
        "test_id": test["id"],
        "test_title": test["title"],
        "test_type": test["test_type"],
        "score": round(score, 2),
        "max_score": max_score,
        "correct_answers": correct,
        "wrong_answers": wrong,
        "unanswered_answers": unanswered,
        "total_questions": total_questions,
        "percentage": percentage,
        "accuracy": accuracy,
        "time_taken_seconds": int(data.get("time_taken_seconds", 0)),
        "answers": answers,
    }))
    return jsonify({"message": "submitted", "redirect_url": url_for("main.result_page", attempt_id=attempt["id"])})


@main_bp.route("/result/<attempt_id>")
@login_required
def result_page(attempt_id):
    user = current_user()
    attempt = normalize(repo.get_attempt(attempt_id))
    if not attempt or attempt["user_id"] != user["id"]:
        return render_template("404.html"), 404
    attempt["section_summary"] = build_attempt_summary(attempt)
    return render_template("result.html", attempt=attempt)


@main_bp.route("/review/<attempt_id>")
@login_required
def review_page(attempt_id):
    user = current_user()
    attempt = normalize(repo.get_attempt(attempt_id))
    if not attempt or attempt["user_id"] != user["id"]:
        return render_template("404.html"), 404
    return render_template("review.html", attempt=attempt)


@main_bp.route("/leaderboard")
@login_required
def leaderboard():
    exam_slug = request.args.get("exam", "").strip()
    attempts = [normalize(item) for item in repo.list_top_attempts(exam_slug=exam_slug or None)]
    exams = build_exam_cards(current_user())
    return render_template("leaderboard.html", attempts=attempts, exams=exams, selected_exam=exam_slug)


@main_bp.route("/profile")
@login_required
def profile():
    user = current_user()
    attempts = [normalize(item) for item in repo.list_attempts_for_user(user["id"])]
    purchases = [normalize(item) for item in repo.list_user_purchases(user["id"])]
    average = round(sum(item["percentage"] for item in attempts) / len(attempts), 1) if attempts else 0
    return render_template("profile.html", attempts=attempts, purchases=purchases, average=average)
