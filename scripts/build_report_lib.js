// build_report_lib.js -- shared helpers for the report builder.
const fs = require('fs');
const path = require('path');
const d = require('docx');
const {Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
       WidthType, ShadingType, BorderStyle, ImageRun, PageBreak} = d;

const INK = '1A1A1A', MUTED = '5A5A5A', RULE = 'D6D6D0', HEAD = '1F3864',
      CODEBG = 'F4F4F1', HDRBG = 'E8EDF5';
const PAGE_W = 9026;   // A4 content width in DXA (11906 - 2*1440)

const B = path.join(__dirname, '..');
const D = JSON.parse(fs.readFileSync(path.join(B, 'docs', 'report_data.json'), 'utf8'));

const n = (x, dp = 0) => Number(x).toLocaleString('en-US',
  {minimumFractionDigits: dp, maximumFractionDigits: dp});
const usd = (x, dp = 2) => '$' + n(x, dp);
const pct = (x, dp = 2) => Number(x).toFixed(dp) + '%';
const mb = b => n(b / 1048576, 1) + ' MB';
const gb = b => n(b / 1073741824, 2) + ' GB';

function P(text, o = {}) {
  return new Paragraph({
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: {after: o.after === undefined ? 96 : o.after, line: 252},
    indent: o.indent,
    children: [new TextRun({text, size: o.size || 20, color: o.color || INK,
                            bold: !!o.bold, italics: !!o.italics,
                            font: o.font || 'Calibri'})]
  });
}
// rich paragraph: array of [text, {bold,italics,code}]
function RP(parts, o = {}) {
  return new Paragraph({
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: {after: o.after === undefined ? 96 : o.after, line: 252},
    children: parts.map(([t, s = {}]) => new TextRun({
      text: t, size: s.size || o.size || 20, color: s.color || INK,
      bold: !!s.bold, italics: !!s.italics,
      font: s.code ? 'Consolas' : 'Calibri'}))
  });
}
function H1(text) {
  return new Paragraph({heading: HeadingLevel.HEADING_1, spacing: {before: 240, after: 130},
    children: [new TextRun({text, size: 30, bold: true, color: HEAD, font: 'Calibri'})]});
}
function H2(text) {
  return new Paragraph({heading: HeadingLevel.HEADING_2, spacing: {before: 180, after: 90},
    children: [new TextRun({text, size: 25, bold: true, color: HEAD, font: 'Calibri'})]});
}
function H3(text) {
  return new Paragraph({heading: HeadingLevel.HEADING_3, spacing: {before: 150, after: 75},
    children: [new TextRun({text, size: 22, bold: true, color: INK, font: 'Calibri'})]});
}
function bullet(text, level = 0) {
  return new Paragraph({numbering: {reference: 'bullets', level},
    spacing: {after: 50, line: 246},
    children: [new TextRun({text, size: 20, color: INK, font: 'Calibri'})]});
}
function bulletRich(parts, level = 0) {
  return new Paragraph({numbering: {reference: 'bullets', level},
    spacing: {after: 50, line: 246},
    children: parts.map(([t, s = {}]) => new TextRun({
      text: t, size: 20, color: INK, bold: !!s.bold, italics: !!s.italics,
      font: s.code ? 'Consolas' : 'Calibri'}))});
}
// monospace evidence / code block
function code(lines, o = {}) {
  const arr = Array.isArray(lines) ? lines : String(lines).split('\n');
  return new Table({
    width: {size: PAGE_W, type: WidthType.DXA},
    columnWidths: [PAGE_W],
    borders: {
      top: {style: BorderStyle.SINGLE, size: 2, color: RULE},
      bottom: {style: BorderStyle.SINGLE, size: 2, color: RULE},
      left: {style: BorderStyle.SINGLE, size: 12, color: '9AA7BC'},
      right: {style: BorderStyle.SINGLE, size: 2, color: RULE},
      insideHorizontal: {style: BorderStyle.NONE}, insideVertical: {style: BorderStyle.NONE}},
    rows: [new TableRow({children: [new TableCell({
      width: {size: PAGE_W, type: WidthType.DXA},
      shading: {type: ShadingType.CLEAR, fill: CODEBG},
      margins: {top: 70, bottom: 70, left: 130, right: 90},
      children: arr.map(l => new Paragraph({
        spacing: {after: 0, line: 194},
        children: [new TextRun({text: l.replace(/\t/g, '    '),
                                font: 'Consolas', size: o.size || 13, color: '25292E'})]}))
    })]})]
  });
}
function caption(text) {
  return new Paragraph({alignment: AlignmentType.LEFT, spacing: {before: 50, after: 150},
    children: [new TextRun({text, size: 16, italics: true, color: MUTED, font: 'Calibri'})]});
}
function table(headers, rows, widths, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const w = widths.map(x => Math.round(x / total * PAGE_W));
  w[w.length - 1] = PAGE_W - w.slice(0, -1).reduce((a, b) => a + b, 0);
  const cell = (t, i, isHead, alignRight) => new TableCell({
    width: {size: w[i], type: WidthType.DXA},
    shading: {type: ShadingType.CLEAR, fill: isHead ? HDRBG : 'FFFFFF'},
    margins: {top: 44, bottom: 44, left: 85, right: 85},
    children: [new Paragraph({
      alignment: alignRight ? AlignmentType.RIGHT : AlignmentType.LEFT,
      spacing: {after: 0, line: 228},
      children: [new TextRun({text: String(t), size: o.size || 15, bold: isHead,
                              color: INK, font: 'Calibri'})]})]});
  const right = o.right || [];
  return new Table({
    width: {size: PAGE_W, type: WidthType.DXA},
    columnWidths: w,
    borders: {
      top: {style: BorderStyle.SINGLE, size: 4, color: '8FA0BD'},
      bottom: {style: BorderStyle.SINGLE, size: 4, color: '8FA0BD'},
      left: {style: BorderStyle.NONE}, right: {style: BorderStyle.NONE},
      insideHorizontal: {style: BorderStyle.SINGLE, size: 2, color: RULE},
      insideVertical: {style: BorderStyle.NONE}},
    rows: [
      ...(o.noHeader ? [] : [new TableRow({tableHeader: true,
        children: headers.map((h, i) => cell(h, i, true, right.includes(i)))})]),
      ...rows.map(r => new TableRow({
        children: r.map((c, i) => cell(c, i, false, right.includes(i)))}))]
  });
}
function figure(file, widthPx, heightPx) {
  return new Paragraph({alignment: AlignmentType.CENTER, spacing: {before: 90, after: 30},
    children: [new ImageRun({type: 'png',
      data: fs.readFileSync(path.join(B, 'charts', file)),
      transformation: {width: widthPx, height: heightPx}})]});
}
function pyfile(rel, o = {}) {
  let lines = fs.readFileSync(path.join(B, rel), 'utf8').split('\n');
  if (o.from !== undefined) lines = lines.slice(o.from, o.to);
  if (o.stripDoc) {                       // drop the module docstring
    let i = lines.findIndex(l => l.startsWith('"""'));
    if (i >= 0) { let j = lines.findIndex((l, k) => k > i && l.includes('"""')); lines = lines.slice(j + 1); }
  }
  while (lines.length && lines[0].trim() === '') lines.shift();
  while (lines.length && lines[lines.length - 1].trim() === '') lines.pop();
  return code(lines, {size: 14});
}
function evidence(rel, from, to) {
  const lines = fs.readFileSync(path.join(B, rel), 'utf8').split('\n')
    .filter(l => !l.includes('NativeCodeLoader'));
  return code(lines.slice(from, to), {size: 14});
}
function grepEvidence(rel, patterns, max) {
  const lines = fs.readFileSync(path.join(B, rel), 'utf8').split('\n')
    .filter(l => !l.includes('NativeCodeLoader'))
    .filter(l => patterns.some(p => l.includes(p)));
  return code(lines.slice(0, max || 60).map(l => l.replace(/^\t+/, '  ')), {size: 14});
}
// static contents line with a right-aligned page number and dot leader
function tocLine(text, page, o = {}) {
  return new Paragraph({
    spacing: {after: 60, line: 252},
    indent: {left: o.sub ? 340 : 0},
    tabStops: [{type: d.TabStopType.RIGHT, position: PAGE_W, leader: d.LeaderType.DOT}],
    children: [
      new TextRun({text, size: o.sub ? 19 : 20, bold: !o.sub, color: INK, font: 'Calibri'}),
      new TextRun({children: [new d.Tab()], size: o.sub ? 19 : 20, color: MUTED, font: 'Calibri'}),
      new TextRun({text: String(page), size: o.sub ? 19 : 20, color: INK, font: 'Calibri'})]});
}

const pb = () => new Paragraph({children: [new PageBreak()]});

module.exports = {d, D, P, RP, H1, H2, H3, bullet, bulletRich, code, caption, table, tocLine,
                  figure, pyfile, evidence, grepEvidence, pb, n, usd, pct, mb, gb,
                  PAGE_W, INK, MUTED, HEAD, B};
