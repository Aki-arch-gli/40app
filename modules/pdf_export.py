from reportlab.pdfgen import canvas

def export_pdf(menu):

    pdf = canvas.Canvas("献立表.pdf")

    y = 800

    pdf.drawString(
        100,
        y,
        "Today's Menu"
    )

    y -= 40

    for meal, food in menu.items():

        pdf.drawString(
            100,
            y,
            meal
        )

        pdf.drawString(
            200,
            y,
            food["料理名"]
        )

        y -= 30

    pdf.save()

    return "献立表.pdf"