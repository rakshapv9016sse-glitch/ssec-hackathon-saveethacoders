import io
import math

from PIL import Image, ImageDraw, ImageFont


PALETTE = {
    "elephant": "#8D9CAF", "cat": "#E6A15C", "dog": "#B98559",
    "butterfly": "#E7799B", "fish": "#56A9CF", "bird": "#E5B74F",
    "flower": "#ED7897", "tree": "#54A875", "leaf": "#59A36C",
    "sun": "#F5C64B", "cloud": "#8BC4E8", "alphabet": "#6C7DE8",
    "number": "#6C7DE8", "shapes": "#8B6BE8", "science": "#50A7A0",
    "fruit": "#E9794E",
}


def _shape(draw, subject, bounds, fill, outline, width):
    left, top, right, bottom = bounds
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    span = min(right - left, bottom - top)
    line = max(2, int(span * 0.025))
    if subject in ("elephant", "cat", "dog"):
        if subject == "elephant":
            draw.ellipse((left + .12 * span, top + .28 * span, right - .12 * span, bottom - .08 * span), fill=fill, outline=outline, width=line)
            draw.ellipse((left + .10 * span, top + .08 * span, left + .46 * span, top + .58 * span), fill=fill, outline=outline, width=line)
            draw.ellipse((right - .46 * span, top + .08 * span, right - .10 * span, top + .58 * span), fill=fill, outline=outline, width=line)
            draw.ellipse((left + .29 * span, top + .18 * span, right - .29 * span, top + .72 * span), fill=fill, outline=outline, width=line)
            draw.arc((center_x - .10 * span, center_y - .06 * span, center_x + .22 * span, bottom), 15, 270, fill=outline, width=max(line, int(span * .06)))
        else:
            if subject == "cat":
                draw.polygon([(left + .20 * span, top + .38 * span), (left + .20 * span, top + .08 * span), (left + .43 * span, top + .25 * span)], fill=fill, outline=outline)
                draw.polygon([(right - .20 * span, top + .38 * span), (right - .20 * span, top + .08 * span), (right - .43 * span, top + .25 * span)], fill=fill, outline=outline)
            else:
                draw.ellipse((left + .08 * span, top + .20 * span, left + .40 * span, top + .62 * span), fill=fill, outline=outline, width=line)
                draw.ellipse((right - .40 * span, top + .20 * span, right - .08 * span, top + .62 * span), fill=fill, outline=outline, width=line)
            draw.ellipse((left + .20 * span, top + .18 * span, right - .20 * span, bottom - .08 * span), fill=fill, outline=outline, width=line)
        eye_y = top + .43 * span
        draw.ellipse((center_x - .16 * span, eye_y, center_x - .11 * span, eye_y + .05 * span), fill=outline)
        draw.ellipse((center_x + .11 * span, eye_y, center_x + .16 * span, eye_y + .05 * span), fill=outline)
    elif subject == "butterfly":
        for cx, cy, rx, ry in ((left + .30 * span, top + .38 * span, .25, .22), (right - .30 * span, top + .38 * span, .25, .22), (left + .34 * span, top + .68 * span, .18, .18), (right - .34 * span, top + .68 * span, .18, .18)):
            draw.ellipse((cx - rx * span, cy - ry * span, cx + rx * span, cy + ry * span), fill=fill, outline=outline, width=line)
        draw.line((center_x, top + .27 * span, center_x, bottom - .18 * span), fill=outline, width=line * 3)
    elif subject == "fish":
        draw.ellipse((left + .16 * span, top + .28 * span, right - .20 * span, bottom - .24 * span), fill=fill, outline=outline, width=line)
        draw.polygon([(right - .20 * span, center_y), (right, top + .24 * span), (right, bottom - .24 * span)], fill=fill, outline=outline)
        draw.ellipse((left + .30 * span, center_y - .05 * span, left + .36 * span, center_y + .01 * span), fill=outline)
    elif subject == "bird":
        draw.ellipse((left + .18 * span, top + .14 * span, right - .18 * span, bottom - .15 * span), fill=fill, outline=outline, width=line)
        draw.polygon([(right - .22 * span, top + .40 * span), (right, top + .48 * span), (right - .22 * span, top + .57 * span)], fill="#E6A14C", outline=outline)
        draw.ellipse((left + .57 * span, top + .32 * span, left + .63 * span, top + .38 * span), fill=outline)
    elif subject == "flower":
        for angle in range(0, 360, 60):
            cx = center_x + math.cos(math.radians(angle)) * .19 * span
            cy = center_y - .12 * span + math.sin(math.radians(angle)) * .19 * span
            draw.ellipse((cx - .13 * span, cy - .18 * span, cx + .13 * span, cy + .18 * span), fill=fill, outline=outline, width=line)
        draw.ellipse((center_x - .12 * span, center_y - .24 * span, center_x + .12 * span, center_y), fill="#F5C64B", outline=outline, width=line)
        draw.line((center_x, center_y, center_x, bottom - .05 * span), fill=outline, width=line * 3)
    elif subject == "tree":
        draw.rectangle((center_x - .10 * span, center_y, center_x + .10 * span, bottom - .05 * span), fill="#9B6B43", outline=outline, width=line)
        draw.ellipse((left + .18 * span, top + .10 * span, right - .18 * span, center_y + .14 * span), fill=fill, outline=outline, width=line)
    elif subject == "leaf":
        draw.polygon([(left + .12 * span, bottom - .18 * span), (left + .20 * span, top + .24 * span), (right - .14 * span, top + .14 * span), (right - .24 * span, bottom - .20 * span)], fill=fill, outline=outline)
        draw.line((left + .17 * span, bottom - .20 * span, right - .19 * span, top + .19 * span), fill=outline, width=line)
    elif subject == "sun":
        draw.ellipse((center_x - .24 * span, center_y - .24 * span, center_x + .24 * span, center_y + .24 * span), fill=fill, outline=outline, width=line)
        for angle in range(0, 360, 45):
            start = (center_x + math.cos(math.radians(angle)) * .30 * span, center_y + math.sin(math.radians(angle)) * .30 * span)
            end = (center_x + math.cos(math.radians(angle)) * .42 * span, center_y + math.sin(math.radians(angle)) * .42 * span)
            draw.line((start, end), fill=outline, width=line * 2)
    elif subject == "cloud":
        draw.ellipse((left + .15 * span, center_y - .15 * span, center_x + .12 * span, center_y + .18 * span), fill=fill, outline=outline, width=line)
        draw.ellipse((center_x - .10 * span, top + .17 * span, center_x + .25 * span, center_y + .19 * span), fill=fill, outline=outline, width=line)
        draw.ellipse((center_x + .08 * span, center_y - .12 * span, right - .12 * span, center_y + .19 * span), fill=fill, outline=outline, width=line)
        draw.rectangle((left + .25 * span, center_y, right - .22 * span, center_y + .18 * span), fill=fill)
    elif subject in ("alphabet", "number"):
        draw.rounded_rectangle(bounds, radius=int(span * .06), fill=fill, outline=outline, width=line)
        try:
            font = ImageFont.load_default(size=int(span * .50))
        except TypeError:
            font = ImageFont.load_default()
        draw.text((center_x, center_y), "A" if subject == "alphabet" else "1", fill="white", anchor="mm", font=font)
    elif subject == "shapes":
        draw.ellipse((left + .08 * span, top + .28 * span, left + .44 * span, top + .64 * span), fill=fill, outline=outline, width=line)
        draw.rectangle((left + .48 * span, top + .28 * span, right - .08 * span, top + .64 * span), fill="#F2BD52", outline=outline, width=line)
        draw.polygon([(center_x, bottom - .04 * span), (left + .48 * span, top + .70 * span), (right - .06 * span, top + .70 * span)], fill="#5BB89C", outline=outline)
    elif subject == "science":
        draw.line((center_x - .10 * span, top + .20 * span, center_x - .10 * span, center_y, left + .20 * span, bottom - .18 * span, right - .20 * span, bottom - .18 * span, center_x + .10 * span, center_y, center_x + .10 * span, top + .20 * span), fill=outline, width=line * 3)
        draw.line((left + .28 * span, bottom - .34 * span, right - .28 * span, bottom - .34 * span), fill="#50A7A0", width=line * 5)
    else:
        draw.ellipse((left + .20 * span, top + .22 * span, right - .20 * span, bottom - .12 * span), fill=fill, outline=outline, width=line)
        draw.line((center_x, top + .25 * span, center_x + .10 * span, top + .12 * span), fill=outline, width=line * 2)


def render_fallback_png(subject, purpose, width, height, grade_group="Grade 2"):
    worksheet = purpose == "coloring_worksheet"
    background = "#FFFFFF" if worksheet else "#F7F8FC"
    foreground = "#000000" if worksheet else "#20242C"
    fill = "#FFFFFF" if worksheet else PALETTE[subject]
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    scale = min(width, height)
    if purpose == "coloring_worksheet":
        draw.text((width / 2, height * .08), f"Color the {subject}", fill=foreground, anchor="mm")
        bounds = (width * .15, height * .20, width * .85, height * .80)
    elif purpose == "educational_flashcard":
        draw.rounded_rectangle((width * .06, height * .05, width * .94, height * .77), radius=int(scale * .03), fill="white", outline="#E1E5ED", width=max(2, int(scale * .008)))
        bounds = (width * .16, height * .10, width * .84, height * .73)
        draw.text((width / 2, height * .85), subject.title(), fill=foreground, anchor="mm")
        draw.text((width / 2, height * .93), grade_group, fill="#667085", anchor="mm")
    else:
        draw.rectangle((width * .04, height * .035, width * .96, height * .23), fill="#263B67")
        draw.text((width / 2, height * .105), f"Explore {subject.title()}", fill="white", anchor="mm")
        draw.text((width / 2, height * .18), f"A learning poster for {grade_group}", fill="#E7EDFF", anchor="mm")
        bounds = (width * .18, height * .25, width * .82, height * .75)
        draw.rounded_rectangle((width * .08, height * .81, width * .92, height * .94), radius=int(scale * .02), fill="white", outline="#DFE4ED", width=max(2, int(scale * .006)))
        draw.text((width / 2, height * .875), "Observe - Learn - Discover", fill="#263B67", anchor="mm")
    _shape(draw, subject, bounds, fill, foreground, max(2, int(scale * .01)))
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()