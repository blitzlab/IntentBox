import joblib, pandas as pd
from django.core.management.base import BaseCommand
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

class Command(BaseCommand):
    help = "Train intent classifier for inbox messages."

    def add_arguments(self, parser):
        parser.add_argument("--data", default="data/inbox_seed.csv")
        parser.add_argument("--out", default="models/intent_clf.joblib")

    def handle(self, *args, **opts):
        df = pd.read_csv(opts["data"])
        X, y = df["text"].astype(str).tolist(), df["intent"].tolist()

        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=2)),
            ("clf", LogisticRegression(max_iter=1000, n_jobs=None))
        ])
        pipe.fit(X, y)
        joblib.dump(pipe, opts["out"])
        self.stdout.write(self.style.SUCCESS(f"Saved model -> {opts['out']}"))