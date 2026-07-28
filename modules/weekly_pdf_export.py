from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def export_weekly_pdf(text):

    filename = "AI週間献立表.pdf"

    doc = SimpleDocTemplate(
        filename
    )

    styles = getSampleStyleSheet()

    story = []


    title = Paragraph(
        "AI週間献立表",
        styles["Title"]
    )

    story.append(title)

    story.append(
        Spacer(1,20)
    )


    for line in text.split("\n"):

        if line.strip():

            p = Paragraph(
                line,
                styles["Normal"]
            )

            story.append(p)

            story.append(
                Spacer(1,8)
            )


    doc.build(
        story
    )


    return filename