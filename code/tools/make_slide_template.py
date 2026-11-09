# make_slide_template.py : derive the pandoc reference template for the slide decks from the NIDI PowerPoint template.
#   python3 code/tools/make_slide_template.py            (from the project root)
# Input:  docs/slides/template/NIDI_template.pptx   (NIDI's own template, as received; 4:3)
# Output: docs/slides/template/nidi_reference.pptx  (used by code/tools/make_deck.py via pandoc --reference-doc)
#
# Run only when the NIDI template changes; the reference template is kept in the repository, so building a deck does
# not need this script or its dependency (python-pptx).
#
# The NIDI template carries its design on example slides (a full-page background picture with text boxes on top),
# while its layouts are bare and named in Dutch.  pandoc fills layouts by their English names, so this script
#   - renames the layouts pandoc uses (Title Slide, Title and Content, Section Header, Two Content, Comparison,
#     Content with Caption, Title Only, Blank);
#   - places the background picture of the matching example slide in each layout, behind the placeholders:
#       orange title page  -> Title Slide              orange closing page -> Section Header
#       white text page    -> Title and Content        white table/figure page -> the two-column and other layouts
#   - positions the placeholders on the text areas of those pages and gives them the template's type (Arial; titles
#     bold 28 pt black on the text page, bold 20 pt red on the table page, white on the orange pages);
#   - sets the theme to the NIDI colours (accent 1 = NIDI orange, so pandoc's tables get an orange header row) and Arial;
#   - adds a page number to the content layouts and removes the example slides.
import os, sys, copy
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
SRC = os.path.join(ROOT, "docs", "slides", "template", "NIDI_template.pptx")
OUT = os.path.join(ROOT, "docs", "slides", "template", "nidi_reference.pptx")

ORANGE, RED, INK, GREY, WHITE = "FE450D", "FC2E11", "1A1A1A", "7F7F7F", "FFFFFF"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"a": A, "p": P, "r": R}

# example slides whose background picture each kind of page uses (0-based, in the NIDI template)
BACKGROUND = {"title": 3, "text": 5, "wide": 7, "section": 9}

# layout (Dutch name in the template) -> (pandoc name, page kind, {placeholder idx: (left, top, width, height) in inches})
TEXT_BODY = (1.2, 1.95, 7.8, 4.6)
LAYOUTS = {
    "Titeldia": ("Title Slide", "title", {0: (1.6, 1.5, 6.8, 1.9), 1: (1.6, 3.6, 6.8, 2.2)}),
    "Titel en object": ("Title and Content", "text", {0: (1.2, 0.95, 7.8, 0.9), 1: TEXT_BODY}),
    "Sectiekop": ("Section Header", "section", {0: (1.6, 1.5, 6.8, 1.6), 1: (1.6, 3.4, 6.8, 2.6)}),
    "Inhoud van twee": ("Two Content", "wide", {0: (0.6, 0.35, 8.6, 0.6), 1: (0.6, 1.1, 4.2, 5.4), 2: (5.0, 1.1, 4.2, 5.4)}),
    "Vergelijking": ("Comparison", "wide", {0: (0.6, 0.35, 8.6, 0.6), 1: (0.6, 1.1, 4.2, 0.5), 2: (0.6, 1.65, 4.2, 4.85),
                                             3: (5.0, 1.1, 4.2, 0.5), 4: (5.0, 1.65, 4.2, 4.85)}),
    # pandoc uses this layout for a slide with a lead sentence followed by a table or picture: sentence on top, table below
    "Inhoud met bijschrift": ("Content with Caption", "wide", {0: (0.6, 0.35, 8.6, 0.6), 2: (0.6, 1.05, 8.6, 0.75), 1: (0.6, 1.9, 8.6, 4.65)}),
    "Alleen titel": ("Title Only", "wide", {0: (0.6, 0.35, 8.6, 0.6)}),
    "Leeg": ("Blank", "wide", {}),
}
# type per page kind: (title size, title colour, body size, body colour)
STYLE = {"title": (32, WHITE, 18, WHITE), "section": (36, WHITE, 18, WHITE),
         "text": (28, INK, 16, INK), "wide": (20, RED, 16, INK)}
PAGE_NUMBER = {"text": (8.1, 6.95, 1.0, 0.25), "wide": (8.1, 6.62, 1.0, 0.25)}   # clear of the logo and the dot lines


def emu(v):
    return str(int(Inches(v)))


def run_props(size, colour, bold):
    rp = etree.Element(f"{{{A}}}defRPr", sz=str(size * 100), b="1" if bold else "0")
    fill = etree.SubElement(rp, f"{{{A}}}solidFill")
    etree.SubElement(fill, f"{{{A}}}srgbClr", val=colour)
    etree.SubElement(rp, f"{{{A}}}latin", typeface="Arial")
    etree.SubElement(rp, f"{{{A}}}cs", typeface="Arial")
    return rp


def set_list_style(sp, levels):
    """levels: list of (size, colour, bold, bullet) for lvl1.. ; written as the placeholder's own list style."""
    body = sp.find("p:txBody", NS)
    old = body.find("a:lstStyle", NS)
    new = etree.Element(f"{{{A}}}lstStyle")
    for i, (size, colour, bold, bullet) in enumerate(levels, start=1):
        attrs = {}
        if bullet:
            attrs = {"marL": str(int(Inches(0.22 + 0.25 * (i - 1)))), "indent": str(-int(Inches(0.2)))}
        else:
            attrs = {"marL": "0", "indent": "0"}
        pp = etree.SubElement(new, f"{{{A}}}lvl{i}pPr", **attrs)
        sb = etree.SubElement(pp, f"{{{A}}}spcBef")
        etree.SubElement(sb, f"{{{A}}}spcPts", val=str(int(size * 40)))   # 0.4 line before each paragraph
        if bullet:
            bc = etree.SubElement(pp, f"{{{A}}}buClr")
            etree.SubElement(bc, f"{{{A}}}srgbClr", val=ORANGE)
            etree.SubElement(pp, f"{{{A}}}buFont", typeface="Arial")
            etree.SubElement(pp, f"{{{A}}}buChar", char="•")
        else:
            etree.SubElement(pp, f"{{{A}}}buNone")
        pp.append(run_props(size, colour, bold))
    if old is not None:
        body.replace(old, new)
    else:
        body.insert(1, new)


def background(layout, image_part, name="NIDI background"):
    rid = layout.part.relate_to(image_part, RT.IMAGE)
    pic = etree.fromstring(
        f'<p:pic xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:nvPicPr><p:cNvPr id="900" name="{name}"/>'
        f'<p:cNvPicPr><a:picLocks noGrp="1" noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>'
        f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
        f'<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="9144000" cy="6858000"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
    tree = layout.shapes._spTree
    tree.insert(2, pic)                                   # after nvGrpSpPr and grpSpPr: painted first, behind the rest


def page_number(layout, box):
    x, y, w, h = box
    sp = etree.fromstring(
        f'<p:sp xmlns:p="{P}" xmlns:a="{A}"><p:nvSpPr><p:cNvPr id="901" name="Page number"/><p:cNvSpPr txBox="1"/>'
        f'<p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0"/>'
        f'<a:lstStyle/><a:p><a:pPr algn="r"/><a:fld id="{{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}}" type="slidenum">'
        f'<a:rPr lang="en-GB" sz="1000"><a:solidFill><a:srgbClr val="{GREY}"/></a:solidFill><a:latin typeface="Arial"/></a:rPr>'
        f'<a:t>&#8249;#&#8250;</a:t></a:fld></a:p></p:txBody></p:sp>')
    layout.shapes._spTree.append(sp)


def theme(prs):
    for part in prs.part.package.iter_parts():
        if str(part.partname).startswith("/ppt/theme/"):
            x = etree.fromstring(part.blob)
            scheme = x.find(".//a:clrScheme", NS)
            for tag, val in (("dk2", INK), ("accent1", ORANGE), ("accent2", RED), ("hlink", RED), ("folHlink", GREY)):
                el = scheme.find(f"a:{tag}", NS)
                for c in list(el):
                    el.remove(c)
                etree.SubElement(el, f"{{{A}}}srgbClr", val=val)
            for f in x.findall(".//a:fontScheme/*/a:latin", NS):
                f.set("typeface", "Arial")
            part._blob = etree.tostring(x, xml_declaration=True, encoding="UTF-8", standalone=True)


def main():
    prs = Presentation(SRC)
    pics = {}
    for kind, i in BACKGROUND.items():
        slide = prs.slides[i]
        pic = [s for s in slide.shapes if s.shape_type == 13][0]
        pics[kind] = slide.part.related_part(pic._element.blipFill.blip.rEmbed)
    for layout in prs.slide_layouts:
        dutch = layout.name
        if dutch not in LAYOUTS:
            continue
        name, kind, boxes = LAYOUTS[dutch]
        layout._element.cSld.set("name", name)
        background(layout, pics[kind])
        tsize, tcol, bsize, bcol = STYLE[kind]
        for ph in list(layout.placeholders):
            idx = ph.placeholder_format.idx
            if idx in (10, 11, 12):                          # date, footer, slide number: pandoc does not fill them
                ph._element.getparent().remove(ph._element)
                continue
            if idx not in boxes:
                ph._element.getparent().remove(ph._element)
                continue
            x, y, w, h = boxes[idx]
            ph.left, ph.top, ph.width, ph.height = Inches(x), Inches(y), Inches(w), Inches(h)
            if idx == 0:
                set_list_style(ph._element, [(tsize, tcol, True, False)])
                ph._element.find("p:txBody/a:bodyPr", NS).set("anchor", "b" if kind in ("text",) else "t")
            elif name == "Comparison" and idx in (1, 3):     # column headings
                set_list_style(ph._element, [(bsize + 2, INK, True, False)])
            elif name == "Content with Caption" and idx == 2:
                set_list_style(ph._element, [(bsize + 1, INK, False, False)])
            else:
                big = kind in ("title", "section")
                set_list_style(ph._element, [(bsize, bcol, big, not big), (bsize - 2, bcol, False, not big),
                                             (bsize - 2, bcol, False, not big)])
        if kind in PAGE_NUMBER:
            page_number(layout, PAGE_NUMBER[kind])
    theme(prs)
    ids = prs.slides._sldIdLst
    for sld in list(ids):                                    # the example slides are not part of a reference template
        prs.part.drop_rel(sld.rId)
        ids.remove(sld)
    prs.save(OUT)
    print(f"Reference template written: {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
