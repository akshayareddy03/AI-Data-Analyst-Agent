from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)


# ==================================================
# AI ANALYSIS FUNCTION
# ==================================================

def generate_ai_analysis(df, question):

    q = question.lower().strip()

    cols = [c.lower() for c in df.columns]

    if q == "highest marks":

        if "marks" in cols and "name" in cols:

            marks_col = df.columns[cols.index("marks")]
            name_col = df.columns[cols.index("name")]

            topper = df.loc[df[marks_col].idxmax()]

            return f"""
🏆 Highest Marks Student

Name: {topper[name_col]}

Marks: {topper[marks_col]}
"""

    elif q == "lowest marks":

        if "marks" in cols and "name" in cols:

            marks_col = df.columns[cols.index("marks")]
            name_col = df.columns[cols.index("name")]

            student = df.loc[df[marks_col].idxmin()]

            return f"""
📉 Lowest Marks Student

Name: {student[name_col]}

Marks: {student[marks_col]}
"""

    elif q == "average marks":

        if "marks" in cols:

            marks_col = df.columns[cols.index("marks")]

            return f"""
📊 Average Marks

{round(df[marks_col].mean(), 2)}
"""

    elif q == "highest attendance":

        if "attendance" in cols and "name" in cols:

            attendance_col = df.columns[cols.index("attendance")]
            name_col = df.columns[cols.index("name")]

            row = df.loc[df[attendance_col].idxmax()]

            return f"""
🚀 Highest Attendance

Name: {row[name_col]}

Attendance: {row[attendance_col]}%
"""

    elif q == "lowest attendance":

        if "attendance" in cols and "name" in cols:

            attendance_col = df.columns[cols.index("attendance")]
            name_col = df.columns[cols.index("name")]

            row = df.loc[df[attendance_col].idxmin()]

            return f"""
⚠️ Lowest Attendance

Name: {row[name_col]}

Attendance: {row[attendance_col]}%
"""

    elif q == "average attendance":

        if "attendance" in cols:

            attendance_col = df.columns[cols.index("attendance")]

            return f"""
📈 Average Attendance

{round(df[attendance_col].mean(), 2)}%
"""

    elif q == "missing values":

        return f"""
Missing Values

{df.isnull().sum().sum()}
"""

    return """
Question not recognized.

Try:

highest marks
lowest marks
average marks
highest attendance
lowest attendance
average attendance
missing values
"""


# ==================================================
# CHART GENERATION FUNCTION
# ==================================================

def generate_charts(df):

    generated_charts = []

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    date_cols = []

    for col in df.columns:
        if any(word in col.lower() for word in
               ["date", "month", "year", "time"]):
            date_cols.append(col)

    try:

        # LINE CHART

        if len(date_cols) > 0 and len(numeric_cols) > 0:

            plt.figure(figsize=(8, 5))

            plt.plot(
                df[date_cols[0]],
                df[numeric_cols[0]],
                marker="o"
            )

            plt.title(f"{numeric_cols[0]} Trend")

            plt.xticks(rotation=45)

            plt.tight_layout()

            plt.savefig("static/line_chart.png")

            plt.close()

            generated_charts.append("line_chart.png")

        # BAR CHART

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:

            plt.figure(figsize=(8, 5))

            sns.barplot(
                x=df[categorical_cols[0]],
                y=df[numeric_cols[0]]
            )

            plt.xticks(rotation=45)

            plt.tight_layout()

            plt.savefig("static/bar_chart.png")

            plt.close()

            generated_charts.append("bar_chart.png")

        # PIE CHART

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:

            pie_data = (
                df.groupby(categorical_cols[0])[numeric_cols[0]]
                .sum()
                .head(6)
            )

            plt.figure(figsize=(7, 7))

            pie_data.plot(
                kind="pie",
                autopct="%1.1f%%"
            )

            plt.ylabel("")

            plt.tight_layout()

            plt.savefig("static/pie_chart.png")

            plt.close()

            generated_charts.append("pie_chart.png")

        # HISTOGRAM

        if len(numeric_cols) > 0:

            plt.figure(figsize=(8, 5))

            df[numeric_cols[0]].hist(bins=15)

            plt.title(
                f"{numeric_cols[0]} Distribution"
            )

            plt.tight_layout()

            plt.savefig("static/histogram.png")

            plt.close()

            generated_charts.append("histogram.png")

        # HEATMAP

        if len(numeric_cols) > 1:

            plt.figure(figsize=(8, 5))

            sns.heatmap(
                df[numeric_cols].corr(),
                annot=True,
                cmap="Blues"
            )

            plt.tight_layout()

            plt.savefig("static/heatmap.png")

            plt.close()

            generated_charts.append("heatmap.png")

        # BOXPLOT

        if len(numeric_cols) > 0:

            plt.figure(figsize=(8, 5))

            sns.boxplot(
                data=df[numeric_cols]
            )

            plt.tight_layout()

            plt.savefig("static/boxplot.png")

            plt.close()

            generated_charts.append("boxplot.png")

        # SCATTER PLOT

        if len(numeric_cols) >= 2:

            plt.figure(figsize=(8, 5))

            plt.scatter(
                df[numeric_cols[0]],
                df[numeric_cols[1]]
            )

            plt.xlabel(numeric_cols[0])

            plt.ylabel(numeric_cols[1])

            plt.tight_layout()

            plt.savefig("static/scatter.png")

            plt.close()

            generated_charts.append("scatter.png")

        return generated_charts

    except Exception as e:

        print("Chart Error:", e)

        return []


# ==================================================
# MAIN ROUTE
# ==================================================

@app.route("/", methods=["GET", "POST"])
def index():

    table = None
    answer = None
    charts = []

    filename = None
    error = None

    total_rows = 0
    total_columns = 0
    missing_values = 0
    duplicate_rows = 0

    if request.method == "POST":

        file = request.files.get("file")
        question = request.form.get("question", "")

        if not file:

            error = "Please upload a CSV file."

        elif file.filename == "":

            error = "No file selected."

        elif not file.filename.endswith(".csv"):

            error = "Only CSV files are allowed."

        else:

            try:

                filename = secure_filename(file.filename)

                filepath = os.path.join(
                    UPLOAD_FOLDER,
                    filename
                )

                file.save(filepath)

                df = pd.read_csv(filepath)

                table = df.head(20).to_html(
                    classes="table table-striped",
                    index=False
                )

                total_rows = len(df)

                total_columns = len(df.columns)

                missing_values = int(
                    df.isnull().sum().sum()
                )

                duplicate_rows = int(
                    df.duplicated().sum()
                )

                if question:

                    answer = generate_ai_analysis(
                        df,
                        question
                    )

                charts = generate_charts(df)

            except Exception as e:

                error = f"CSV Error: {str(e)}"

    return render_template(
        "index.html",
        table=table,
        answer=answer,
        charts=charts,
        filename=filename,
        error=error,
        total_rows=total_rows,
        total_columns=total_columns,
        missing_values=missing_values,
        duplicate_rows=duplicate_rows
    )


# ==================================================
# RUN APP
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)