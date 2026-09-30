# Template execution contract

## Reference

- Source: `C:\Users\Rajat Kumar\Desktop\KJSSE\SEM-V\HO-AIACS Lab\Research Paper\IJSRP-paper-format.docx`
- SHA-256: `119C7563246000961199DE79E9DDE11277AB82B39D4DD9987BC9505D8682D1E6`
- Size: 31,879 bytes
- Sections: five in the source; the title block is one column and the article body is two columns through continuous section breaks.
- Render evidence: `.research-work/template-word-render/template.pdf`, exported read-only through Microsoft Word because LibreOffice is not installed on this Windows host.
- Style evidence: `.research-work/template-style-evidence.json` and the section, field, image, and package audits captured during distillation.

## Page system

- US Letter portrait, 8.5 x 11 inches.
- Left and right margins: 0.5 inches.
- First section top and bottom margins: 0.7 inches.
- Body top margin: 0.8 inches; bottom margin: 0.7 inches.
- Two body columns with 0.2-inch spacing, introduced by a continuous section break after the full-width abstract and keywords.
- The source has a default header and footer with a PAGE field. Its sample issue, DOI, licence, and publication text are not valid metadata for the student's paper and will be removed. A simple page-number footer will be retained.

## Typography and components

- Academic journal layout using Times New Roman as the body face.
- Full-width centred title, author names, affiliation, abstract, and index terms.
- Two-column justified body, compact paragraph spacing, first-line indents for ordinary prose.
- Centred upper-case Roman-numbered major section headings and left-aligned lettered subheadings.
- Captions use compact centred text. References use numbered entries and hanging indents.
- Tables use black text, white header backgrounds, visible light borders, compact cell margins, and repeated header rows when a table spans pages.

## Content flow and editable slots

- Rewrite title, authors, affiliation, abstract, index terms, all sample body text, conclusion, and references.
- Preserve the authors and affiliation already present unless the user later corrects them.
- Omit the second author's incomplete ORCID rather than inventing it. Preserve the first author's ORCID only if it remains available in the source.
- Replace sample publication metadata with a simple course-paper footer and dynamic page number.
- Include introduction, related work, problem statement and gap, research questions and objectives, proposed methodology, dataset, implementation and models, XAI methods, experimental setup, evaluation metrics, pending results, explanation and error-analysis plans, discussion, limitations, future work, conclusion, and references.
- Include pending result tables; do not create experimental values.

## Package preservation

- Preserve the source file unchanged.
- Reuse its theme, styles, numbering definitions, font table, and page geometry as the base.
- The document body, header, footer, relationships, settings, and core/app properties are editable because the requested paper replaces the sample manuscript and needs valid fields and metadata.
- Footnotes, endnotes, custom XML, and label metadata may remain only when harmless and unreferenced; they will be checked after authoring.

## Fidelity gates

- The final document must remain recognisably derived from the IJSRP layout: full-width opening block and two-column article body.
- The source hash must remain unchanged.
- The final file must render to approximately eight pages with no clipping, overlap, broken tables, missing glyphs, or malformed headers and footers.
- The final paper must contain no template instructions, dummy references, fake DOI, fabricated experimental results, or internal tool citations.
