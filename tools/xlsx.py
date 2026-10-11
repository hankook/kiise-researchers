# -*- coding: utf-8 -*-
"""
xlsx 최소 읽기·쓰기 — 표준 라이브러리만 사용합니다.

신진연구자 등록 양식을 만들고 읽는 데 필요한 만큼만 구현했습니다.
  read_rows(path)       첫 시트(또는 지정한 이름의 시트)의 셀 값을 문자열 행 목록으로
  build(sheets)         시트 XML 들을 묶어 xlsx 바이트로 (스타일은 아래 STYLES 고정)
  sheet_xml(...)        행·열 너비·병합·드롭다운으로 시트 XML 생성

xlsx 는 XML 파일 몇 개를 zip 으로 묶은 것입니다. 엑셀·한셀·Numbers·구글 시트가
저장한 파일을 모두 읽을 수 있도록 공유 문자열·인라인 문자열·서식 있는 글자를 처리합니다.
"""
import io
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN, "pr": PKG}


# ------------------------------------------------------------------- 읽기
def col_index(ref):
    """'B12' → 1 (0부터)"""
    n = 0
    for ch in re.match(r"[A-Za-z]+", ref).group(0).upper():
        n = n * 26 + ord(ch) - 64
    return n - 1


def _text(node):
    """<si>/<is> 안의 글자. 서식 조각(<r>)은 이어 붙이고 후리가나(<rPh>)는 뺀다."""
    out = []
    for child in node:
        tag = child.tag.split("}")[-1]
        if tag == "t":
            out.append(child.text or "")
        elif tag == "r":
            out.extend(t.text or "" for t in child.findall("m:t", NS))
    return "".join(out)


def _value(c, shared):
    t = c.get("t", "n")
    if t == "inlineStr":
        node = c.find("m:is", NS)
        return _text(node) if node is not None else ""
    v = c.find("m:v", NS)
    v = v.text if v is not None and v.text is not None else ""
    if t == "s":
        return shared[int(v)] if v else ""
    if t == "b":
        return "TRUE" if v == "1" else "FALSE"
    return v


def read_rows(path, prefer_sheet=None):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append(_text(si))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels.findall("pr:Relationship", NS)}
        sheets = wb.findall("m:sheets/m:sheet", NS)
        if not sheets:
            raise ValueError("시트가 없습니다")
        chosen = next((s for s in sheets if s.get("name") == prefer_sheet), sheets[0])
        target = targets[chosen.get("{%s}id" % REL)]
        path_in_zip = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
        root = ET.fromstring(z.read(path_in_zip))

    rows = []
    for row in root.findall("m:sheetData/m:row", NS):
        cells, pos = {}, 0
        for c in row.findall("m:c", NS):
            idx = col_index(c.get("r")) if c.get("r") else pos
            pos = idx + 1
            cells[idx] = _value(c, shared)
        width = max(cells) + 1 if cells else 0
        rows.append([cells.get(i, "") for i in range(width)])
    return rows


# ------------------------------------------------------------------- 쓰기
# 셀 스타일 번호 (STYLES 의 cellXfs 순서)
PLAIN, TITLE, HEADER, LABEL, INPUT, HINT = range(6)

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="5">
<font><sz val="11"/><name val="맑은 고딕"/><family val="2"/></font>
<font><b/><sz val="14"/><color rgb="FF002060"/><name val="맑은 고딕"/><family val="2"/></font>
<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="맑은 고딕"/><family val="2"/></font>
<font><b/><sz val="11"/><name val="맑은 고딕"/><family val="2"/></font>
<font><sz val="10"/><color rgb="FF666666"/><name val="맑은 고딕"/><family val="2"/></font>
</fonts>
<fills count="5">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF002060"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFEEF1F6"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFFFBE6"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border><left style="thin"><color rgb="FFBFBFBF"/></left><right style="thin"><color rgb="FFBFBFBF"/></right><top style="thin"><color rgb="FFBFBFBF"/></top><bottom style="thin"><color rgb="FFBFBFBF"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="6">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="3" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="49" fontId="0" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>
"""


def col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def _cell(ref, value, style):
    if value is None or value == "":
        return '<c r="%s" s="%d"/>' % (ref, style)
    return '<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (
        ref, style, escape(str(value)))


def sheet_xml(rows, widths, merges=(), validations=(), freeze_rows=0, row_heights=None):
    """rows: [[(값, 스타일), ...], ...]   validations: [(셀 범위, [선택지, ...]), ...]"""
    row_heights = row_heights or {}
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="%s" xmlns:r="%s">' % (MAIN, REL)]
    if freeze_rows:
        top = "A%d" % (freeze_rows + 1)
        out.append('<sheetViews><sheetView workbookViewId="0"><pane ySplit="%d" topLeftCell="%s" '
                   'activePane="bottomLeft" state="frozen"/><selection pane="bottomLeft" activeCell="B%d" '
                   'sqref="B%d"/></sheetView></sheetViews>' % (freeze_rows, top, freeze_rows + 1, freeze_rows + 1))
    else:
        out.append('<sheetViews><sheetView workbookViewId="0"/></sheetViews>')
    out.append('<sheetFormatPr defaultRowHeight="16.5"/>')
    out.append("<cols>" + "".join('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i + 1, i + 1, w)
                                  for i, w in enumerate(widths)) + "</cols>")
    out.append("<sheetData>")
    for r, row in enumerate(rows, 1):
        ht = row_heights.get(r)
        attr = ' ht="%s" customHeight="1"' % ht if ht else ""
        out.append('<row r="%d"%s>' % (r, attr) +
                   "".join(_cell(col_letter(c) + str(r), v, s) for c, (v, s) in enumerate(row)) + "</row>")
    out.append("</sheetData>")
    if merges:
        out.append('<mergeCells count="%d">' % len(merges) +
                   "".join('<mergeCell ref="%s"/>' % m for m in merges) + "</mergeCells>")
    if validations:
        out.append('<dataValidations count="%d">' % len(validations))
        for ref, options in validations:
            # showErrorMessage="0": 목록에 없는 값도 직접 입력할 수 있게
            out.append('<dataValidation type="list" allowBlank="1" showErrorMessage="0" sqref="%s">'
                       '<formula1>"%s"</formula1></dataValidation>' % (ref, escape(",".join(options))))
        out.append("</dataValidations>")
    out.append('<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>')
    out.append("</worksheet>")
    return "".join(out)


def build(sheets):
    """sheets: [(시트 이름, 시트 XML), ...] → xlsx 바이트.
    압축하지 않고 시각을 고정해, 같은 내용이면 항상 같은 바이트가 나옵니다 (check 가 비교)."""
    n = len(sheets)
    files = [
        ("[Content_Types].xml",
         '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
         '<Default Extension="xml" ContentType="application/xml"/>'
         '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
         + "".join('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1) for i in range(n))
         + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
         '</Types>'),
        ("_rels/.rels",
         '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<Relationships xmlns="%s"><Relationship Id="rId1" '
         'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
         'Target="xl/workbook.xml"/></Relationships>' % PKG),
        ("xl/workbook.xml",
         '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<workbook xmlns="%s" xmlns:r="%s"><bookViews><workbookView/></bookViews><sheets>' % (MAIN, REL)
         + "".join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(name, {'"': "&quot;"}), i + 1, i + 1)
                   for i, (name, _) in enumerate(sheets))
         + "</sheets></workbook>"),
        ("xl/_rels/workbook.xml.rels",
         '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="%s">' % PKG
         + "".join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                   'Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1) for i in range(n))
         + '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
           'Target="styles.xml"/></Relationships>' % (n + 1)),
        ("xl/styles.xml", STYLES),
    ] + [("xl/worksheets/sheet%d.xml" % (i + 1), xml) for i, (_, xml) in enumerate(sheets)]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for name, text in files:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            z.writestr(info, text.encode("utf-8"))
    return buf.getvalue()
