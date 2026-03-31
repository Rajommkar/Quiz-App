import os
from copy import deepcopy
from datetime import UTC, datetime

import mongomock
from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError
from werkzeug.security import generate_password_hash


def utcnow():
    return datetime.now(UTC)


def serialize(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value


def oid(value):
    return ObjectId(value) if isinstance(value, str) else value


BANKS = {
    "management": [
        {"section": "Quant", "text": "A trader marks a product 25% above cost and gives 10% discount. Profit % is:", "options": {"A": "10", "B": "12.5", "C": "15", "D": "18"}, "correct_option": "B", "explanation": "1.25 x 0.90 = 1.125, so profit is 12.5%."},
        {"section": "LRDI", "text": "If the mean of 10 values is 48, the total is:", "options": {"A": "480", "B": "58", "C": "460", "D": "500"}, "correct_option": "A", "explanation": "Mean x count = total."},
        {"section": "Verbal", "text": "Choose the closest meaning of pragmatic.", "options": {"A": "Idealistic", "B": "Practical", "C": "Abstract", "D": "Emotional"}, "correct_option": "B", "explanation": "Pragmatic means practical."},
        {"section": "Reasoning", "text": "All analysts are readers. Some readers are writers. Which is definitely true?", "options": {"A": "All writers are analysts", "B": "Some analysts are writers", "C": "All analysts are readers", "D": "No readers are writers"}, "correct_option": "C", "explanation": "Only the first statement is guaranteed."},
    ],
    "gmat": [
        {"section": "Quant", "text": "If 3x - 7 = 11, x equals:", "options": {"A": "4", "B": "5", "C": "6", "D": "7"}, "correct_option": "C", "explanation": "3x = 18."},
        {"section": "Data Insights", "text": "Sales rise from 50 to 65. Percentage increase is:", "options": {"A": "15", "B": "25", "C": "30", "D": "35"}, "correct_option": "C", "explanation": "15 on base 50 is 30%."},
        {"section": "Verbal", "text": "Choose the logically coherent sentence.", "options": {"A": "Because demand rose, therefore price fell.", "B": "Although margins shrank, efficiency improved.", "C": "Since policy failed, however it expanded.", "D": "The board approved because yet it collapsed."}, "correct_option": "B", "explanation": "Only option B is coherent."},
        {"section": "Data Insights", "text": "In five ordered values, the median is the:", "options": {"A": "First", "B": "Second", "C": "Third", "D": "Fifth"}, "correct_option": "C", "explanation": "The middle of five values is the third."},
    ],
    "gate": [
        {"section": "Core", "text": "Which data structure follows FIFO?", "options": {"A": "Stack", "B": "Queue", "C": "Heap", "D": "Tree"}, "correct_option": "B", "explanation": "Queue is FIFO."},
        {"section": "Algorithms", "text": "Binary search time complexity is:", "options": {"A": "O(n)", "B": "O(log n)", "C": "O(n log n)", "D": "O(1)"}, "correct_option": "B", "explanation": "Search space halves each step."},
        {"section": "OS", "text": "CPU scheduling decides:", "options": {"A": "Disk block size", "B": "Next process to execute", "C": "Page size", "D": "Index order"}, "correct_option": "B", "explanation": "Scheduler chooses the next ready process."},
        {"section": "DBMS", "text": "3NF removes:", "options": {"A": "Duplicate rows", "B": "Transitive dependencies", "C": "Candidate keys", "D": "Primary keys"}, "correct_option": "B", "explanation": "3NF removes transitive dependencies."},
    ],
    "science": [
        {"section": "Physics", "text": "The SI unit of force is:", "options": {"A": "Joule", "B": "Newton", "C": "Pascal", "D": "Watt"}, "correct_option": "B", "explanation": "Force is measured in newtons."},
        {"section": "Chemistry", "text": "pH below 7 indicates a solution is:", "options": {"A": "Basic", "B": "Neutral", "C": "Acidic", "D": "Saline"}, "correct_option": "C", "explanation": "Acids have pH below 7."},
        {"section": "Math", "text": "Derivative of x^2 is:", "options": {"A": "x", "B": "2x", "C": "x^3", "D": "2"}, "correct_option": "B", "explanation": "d/dx x^2 = 2x."},
        {"section": "Reasoning", "text": "If all samples are sterile and some cultures are samples, then some cultures are:", "options": {"A": "Destroyed", "B": "Sterile", "C": "Unknown", "D": "Mutated"}, "correct_option": "B", "explanation": "Some cultures belong to the sterile set."},
    ],
    "pharma": [
        {"section": "Pharmaceutics", "text": "Bioavailability refers to:", "options": {"A": "Taste", "B": "Fraction reaching systemic circulation", "C": "Shelf size", "D": "Packaging rate"}, "correct_option": "B", "explanation": "Bioavailability measures active drug reaching circulation."},
        {"section": "Pharmacology", "text": "An antagonist usually:", "options": {"A": "Activates receptor", "B": "Blocks response", "C": "Adds color", "D": "Raises pH"}, "correct_option": "B", "explanation": "Antagonists block receptor response."},
        {"section": "Chemistry", "text": "Functional groups matter because they affect:", "options": {"A": "Binding", "B": "Only color", "C": "Invoice format", "D": "Box size"}, "correct_option": "A", "explanation": "Functional groups affect binding and reactivity."},
        {"section": "Biostatistics", "text": "Mode is the value appearing:", "options": {"A": "Least often", "B": "Most often", "C": "Only once", "D": "At random"}, "correct_option": "B", "explanation": "Mode is most frequent."},
    ],
    "law": [
        {"section": "Constitutional Law", "text": "Judicial review means:", "options": {"A": "Police inquiry", "B": "Court review of constitutionality", "C": "Cabinet meeting", "D": "Election filing"}, "correct_option": "B", "explanation": "Courts review laws and executive action."},
        {"section": "Jurisprudence", "text": "Ratio decidendi is the:", "options": {"A": "Court fee", "B": "Binding principle of the judgment", "C": "Judge title", "D": "Case number"}, "correct_option": "B", "explanation": "It is the legal principle behind the decision."},
        {"section": "Contract", "text": "A valid contract requires:", "options": {"A": "Offer and acceptance", "B": "Rumor", "C": "Poster", "D": "Witness only"}, "correct_option": "A", "explanation": "Offer and acceptance are foundational elements."},
        {"section": "Legal Reasoning", "text": "Precedent promotes:", "options": {"A": "Delay", "B": "Confusion", "C": "Consistency", "D": "Secrecy"}, "correct_option": "C", "explanation": "Precedent supports consistency."},
    ],
}


EXAMS = [
    {"slug": "cat", "name": "CAT", "full_name": "Common Admission Test", "stream": "MBA", "duration_minutes": 120, "official_question_count": 68, "sample_question_count": 12, "negative_marks": 1, "default_marks": 3, "difficulty": "Hard", "library_key": "management", "sections": ["VARC", "DILR", "QA"], "hero": "CAT-style mocks and PYQ-labelled papers with percentile-focused analysis."},
    {"slug": "xat", "name": "XAT", "full_name": "Xavier Aptitude Test", "stream": "MBA", "duration_minutes": 180, "official_question_count": 95, "sample_question_count": 12, "negative_marks": 0.25, "default_marks": 1, "difficulty": "Hard", "library_key": "management", "sections": ["Verbal", "DM", "Quant"], "hero": "Decision-making and speed-driven XAT practice."},
    {"slug": "cmat", "name": "CMAT", "full_name": "Common Management Admission Test", "stream": "MBA", "duration_minutes": 180, "official_question_count": 100, "sample_question_count": 12, "negative_marks": 1, "default_marks": 4, "difficulty": "Medium", "library_key": "management", "sections": ["Quant", "LR", "Language"], "hero": "CMAT practice packs with quick review loops."},
    {"slug": "snap", "name": "SNAP", "full_name": "Symbiosis National Aptitude Test", "stream": "MBA", "duration_minutes": 60, "official_question_count": 60, "sample_question_count": 12, "negative_marks": 0.25, "default_marks": 1, "difficulty": "Medium", "library_key": "management", "sections": ["English", "Analytical", "Quant"], "hero": "Fast SNAP simulations built for speed and accuracy."},
    {"slug": "nmat", "name": "NMAT", "full_name": "NMAT by GMAC", "stream": "MBA", "duration_minutes": 120, "official_question_count": 108, "sample_question_count": 12, "negative_marks": 0, "default_marks": 3, "difficulty": "Medium", "library_key": "management", "sections": ["Language", "LR", "Quant"], "hero": "Clean NMAT-style pacing and mock review."},
    {"slug": "gmat", "name": "GMAT", "full_name": "GMAT Focus Edition", "stream": "Management", "duration_minutes": 135, "official_question_count": 64, "sample_question_count": 10, "negative_marks": 0, "default_marks": 1, "difficulty": "Hard", "library_key": "gmat", "sections": ["Quant", "Verbal", "Data Insights"], "hero": "GMAT-style practice for Indian and global applicants."},
    {"slug": "gate-cse", "name": "GATE CSE", "full_name": "GATE - Computer Science", "stream": "M.Tech", "duration_minutes": 180, "official_question_count": 65, "sample_question_count": 10, "negative_marks": 0.33, "default_marks": 1, "difficulty": "Hard", "library_key": "gate", "sections": ["GA", "Core", "Math"], "hero": "Core CS mock and PYQ prep for GATE."},
    {"slug": "gate-da", "name": "GATE DA", "full_name": "GATE - Data Science & AI", "stream": "M.Tech", "duration_minutes": 180, "official_question_count": 65, "sample_question_count": 10, "negative_marks": 0.33, "default_marks": 1, "difficulty": "Hard", "library_key": "gate", "sections": ["GA", "Math", "Data"], "hero": "GATE DA practice with aptitude and data-centric sets."},
    {"slug": "iit-jam", "name": "IIT JAM", "full_name": "Joint Admission Test for Masters", "stream": "M.Sc", "duration_minutes": 180, "official_question_count": 60, "sample_question_count": 10, "negative_marks": 0.33, "default_marks": 1, "difficulty": "Medium", "library_key": "science", "sections": ["Science", "Math", "Reasoning"], "hero": "JAM-style science practice with review support."},
    {"slug": "cuet-pg", "name": "CUET PG", "full_name": "Common University Entrance Test - PG", "stream": "University PG", "duration_minutes": 90, "official_question_count": 75, "sample_question_count": 10, "negative_marks": 1, "default_marks": 4, "difficulty": "Medium", "library_key": "science", "sections": ["Domain", "General"], "hero": "CUET PG packs for central university aspirants."},
    {"slug": "gpat", "name": "GPAT", "full_name": "Graduate Pharmacy Aptitude Test", "stream": "M.Pharm", "duration_minutes": 180, "official_question_count": 125, "sample_question_count": 10, "negative_marks": 1, "default_marks": 4, "difficulty": "Medium", "library_key": "pharma", "sections": ["Pharma", "Chem", "Stats"], "hero": "GPAT practice with pharmacy-first analytics."},
    {"slug": "clat-pg", "name": "CLAT PG", "full_name": "Common Law Admission Test - PG", "stream": "LL.M", "duration_minutes": 120, "official_question_count": 120, "sample_question_count": 10, "negative_marks": 0.25, "default_marks": 1, "difficulty": "Medium", "library_key": "law", "sections": ["Consti", "Jurisprudence", "Legal Reasoning"], "hero": "CLAT PG full mocks and legal reasoning review."},
]


def build_questions(exam, label, offset):
    bank = BANKS[exam["library_key"]]
    items = []
    for index in range(exam["sample_question_count"]):
        base = deepcopy(bank[(offset + index) % len(bank)])
        base["question_key"] = f"{exam['slug']}-{label}-{index + 1}"
        base["marks"] = exam["default_marks"]
        base["negative_marks"] = exam["negative_marks"]
        items.append(base)
    return items


def seed_docs():
    exams, tests, plans = [], [], []
    for exam_index, exam in enumerate(EXAMS):
        exams.append({**exam, "stats": {"pyq_years": 5, "mock_sets": 3}, "faq": ["PYQ-only and mock-only passes are available.", "A combo pass unlocks both PYQs and mocks.", "Seeded content is representative and ready for verified PYQ imports."]})
        prices = (299, 499, 699)
        if exam["slug"] in {"gmat", "gate-cse", "gate-da"}:
            prices = (349, 599, 849)
        plans.extend([
            {"slug": f"{exam['slug']}-pyq-pass", "exam_slug": exam["slug"], "title": f"{exam['name']} PYQ Pass", "description": "Last 5 year-wise PYQ-labelled papers.", "price": prices[0], "access_tiers": ["pyq"], "exam_slugs": [exam["slug"]], "features": ["5 PYQ papers", "Solutions and review", "Reattempt anytime"], "recommended": False},
            {"slug": f"{exam['slug']}-mock-pass", "exam_slug": exam["slug"], "title": f"{exam['name']} Mock Pass", "description": "All full mocks for one exam.", "price": prices[1], "access_tiers": ["mock"], "exam_slugs": [exam["slug"]], "features": ["3 full mocks", "Timer and palette", "Analytics"], "recommended": False},
            {"slug": f"{exam['slug']}-complete-pass", "exam_slug": exam["slug"], "title": f"{exam['name']} Complete Pack", "description": "PYQs plus mocks for one exam.", "price": prices[2], "access_tiers": ["pyq", "mock"], "exam_slugs": [exam["slug"]], "features": ["All PYQs", "All mocks", "Best value"], "recommended": True},
        ])
        for year_index, year in enumerate(range(2025, 2020, -1)):
            tests.append({"slug": f"{exam['slug']}-pyq-{year}", "exam_slug": exam["slug"], "title": f"{exam['name']} PYQ {year}", "subtitle": f"Year-wise PYQ-labelled paper {year}", "test_type": "pyq", "access_tier": "pyq", "year": year, "duration_minutes": exam["duration_minutes"], "difficulty": exam["difficulty"], "negative_marks": exam["negative_marks"], "instructions": ["Use the question palette to navigate.", "The full-paper timer runs continuously.", "This demo uses representative exam-style content."], "questions": build_questions(exam, f"pyq-{year}", exam_index + year_index), "is_free": year == 2025})
        for mock_index in range(1, 4):
            tests.append({"slug": f"{exam['slug']}-mock-{mock_index}", "exam_slug": exam["slug"], "title": f"{exam['name']} Full Mock {mock_index}", "subtitle": f"Exam-style simulation {mock_index}", "test_type": "mock", "access_tier": "mock", "year": None, "duration_minutes": exam["duration_minutes"], "difficulty": exam["difficulty"], "negative_marks": exam["negative_marks"], "instructions": ["Attempt in one sitting for best benchmarking.", "Bookmark and mark for review whenever needed.", "Review section-wise analytics after submission."], "questions": build_questions(exam, f"mock-{mock_index}", exam_index + mock_index + 5), "is_free": mock_index == 1})
    plans.append({"slug": "pg-all-access-pass", "exam_slug": "all", "title": "PG All Access Pass", "description": "Unlock PYQs and mocks across the major PG entrance exams.", "price": 3999, "access_tiers": ["pyq", "mock"], "exam_slugs": ["*"], "features": ["All major exams", "Single checkout", "Best value"], "recommended": True})
    return exams, tests, plans


class MongoRepository:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_mock = False

    def init_app(self, app):
        uri = os.environ.get("MONGO_URI", app.config.get("MONGO_URI", "mongodb://127.0.0.1:27017"))
        db_name = os.environ.get("MONGO_DB_NAME", app.config.get("MONGO_DB_NAME", "mockprep_india"))
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=1500)
            self.client.admin.command("ping")
        except PyMongoError:
            self.client = mongomock.MongoClient()
            self.is_mock = True
        self.db = self.client[db_name]
        self.db.users.create_index([("email", ASCENDING)], unique=True)
        self.db.exams.create_index([("slug", ASCENDING)], unique=True)
        self.db.tests.create_index([("slug", ASCENDING)], unique=True)
        self.db.plans.create_index([("slug", ASCENDING)], unique=True)
        app.extensions["mongo_repo"] = self
        app.config["MONGO_ACTIVE_MODE"] = "mongomock" if self.is_mock else "mongodb"

    def seed_database(self):
        exams, tests, plans = seed_docs()
        for exam in exams:
            self.db.exams.update_one({"slug": exam["slug"]}, {"$set": exam}, upsert=True)
        for test in tests:
            self.db.tests.update_one({"slug": test["slug"]}, {"$set": test}, upsert=True)
        for plan in plans:
            self.db.plans.update_one({"slug": plan["slug"]}, {"$set": plan}, upsert=True)
        if not self.db.users.find_one({"email": "demo@mockprep.local"}):
            self.db.users.insert_one({"name": "Demo Aspirant", "email": "demo@mockprep.local", "password_hash": generate_password_hash("password123"), "phone": "", "created_at": utcnow()})

    def create_user(self, name, email, password, phone=""):
        result = self.db.users.insert_one({"name": name, "email": email.lower(), "password_hash": generate_password_hash(password), "phone": phone, "created_at": utcnow()})
        return self.get_user_by_id(result.inserted_id)

    def get_user_by_email(self, email):
        item = self.db.users.find_one({"email": email.lower()})
        return serialize(item) if item else None

    def get_user_by_id(self, user_id):
        item = self.db.users.find_one({"_id": oid(user_id)})
        return serialize(item) if item else None

    def list_exams(self):
        return [serialize(item) for item in self.db.exams.find().sort("name", ASCENDING)]

    def get_exam(self, slug):
        item = self.db.exams.find_one({"slug": slug})
        return serialize(item) if item else None

    def list_tests(self, exam_slug=None, test_type=None):
        query = {}
        if exam_slug:
            query["exam_slug"] = exam_slug
        if test_type:
            query["test_type"] = test_type
        return [serialize(item) for item in self.db.tests.find(query).sort([("exam_slug", ASCENDING), ("title", ASCENDING)])]

    def get_test(self, test_id=None, slug=None):
        query = {"_id": oid(test_id)} if test_id else {"slug": slug}
        item = self.db.tests.find_one(query)
        return serialize(item) if item else None

    def list_plans(self, exam_slug=None):
        query = {}
        if exam_slug and exam_slug != "all":
            query["$or"] = [{"exam_slug": exam_slug}, {"exam_slug": "all"}]
        return [serialize(item) for item in self.db.plans.find(query).sort([("price", ASCENDING), ("title", ASCENDING)])]

    def get_plan(self, slug):
        item = self.db.plans.find_one({"slug": slug})
        return serialize(item) if item else None

    def list_user_purchases(self, user_id):
        return [serialize(item) for item in self.db.purchases.find({"user_id": str(user_id), "status": "completed"}).sort("created_at", -1)]

    def get_purchase(self, purchase_id):
        item = self.db.purchases.find_one({"_id": oid(purchase_id)})
        return serialize(item) if item else None

    def create_purchase(self, user_id, plan, payment_method):
        existing = self.db.purchases.find_one({"user_id": str(user_id), "plan_slug": plan["slug"], "status": "completed"})
        if existing:
            return serialize(existing), False
        doc = {"user_id": str(user_id), "plan_id": plan["id"], "plan_slug": plan["slug"], "plan_title": plan["title"], "exam_slugs": plan["exam_slugs"], "access_tiers": plan["access_tiers"], "amount": plan["price"], "payment_method": payment_method, "status": "completed", "transaction_ref": f"DEMO-{str(ObjectId())[-6:].upper()}", "created_at": utcnow()}
        inserted = self.db.purchases.insert_one(doc)
        return self.get_purchase(inserted.inserted_id), True

    def access_profile(self, user_id):
        profile = {"all": set(), "exam": {}}
        for purchase in self.list_user_purchases(user_id):
            tiers = set(purchase.get("access_tiers", []))
            if "*" in purchase.get("exam_slugs", []):
                profile["all"].update(tiers)
                continue
            for exam_slug in purchase.get("exam_slugs", []):
                profile["exam"].setdefault(exam_slug, set()).update(tiers)
        return profile

    def user_has_access(self, user_id, test):
        if test.get("is_free"):
            return True
        profile = self.access_profile(user_id)
        tier = test["access_tier"]
        return tier in profile["all"] or tier in profile["exam"].get(test["exam_slug"], set())

    def summarize_exam_access(self, user_id, exam_slug):
        profile = self.access_profile(user_id)
        tiers = set(profile["all"]) | set(profile["exam"].get(exam_slug, set()))
        return {"pyq": "pyq" in tiers, "mock": "mock" in tiers, "complete": {"pyq", "mock"}.issubset(tiers)}

    def create_attempt(self, payload):
        payload["created_at"] = utcnow()
        payload["submitted"] = True
        inserted = self.db.attempts.insert_one(payload)
        return self.get_attempt(inserted.inserted_id)

    def get_attempt(self, attempt_id):
        item = self.db.attempts.find_one({"_id": oid(attempt_id)})
        return serialize(item) if item else None

    def list_attempts_for_user(self, user_id, limit=None):
        cursor = self.db.attempts.find({"user_id": str(user_id)}).sort("created_at", -1)
        if limit:
            cursor = cursor.limit(limit)
        return [serialize(item) for item in cursor]

    def list_top_attempts(self, exam_slug=None, limit=20):
        query = {"submitted": True}
        if exam_slug:
            query["exam_slug"] = exam_slug
        return [serialize(item) for item in self.db.attempts.find(query).sort([("percentage", -1), ("time_taken_seconds", ASCENDING)]).limit(limit)]


repo = MongoRepository()
