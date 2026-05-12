// Simple markdown-to-HTML converter for index.md structure
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function parseInline(text: string): string {
  // Links: [text](url)
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  // Bold: **text**
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  // Inline code: `text`
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  return text;
}

function parseTable(lines: string[]): string {
  const rows = lines.map((l) =>
    l
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((c) => c.trim())
  );

  const header = rows[0];
  // rows[1] is the separator line (---|---|...)
  const body = rows.slice(2);

  const thead = header
    .map((h) => `<th>${parseInline(h)}</th>`)
    .join("");
  const tbody = body
    .map((row) => {
      const cells = row.map((c) => `<td>${parseInline(c)}</td>`).join("");
      return `<tr>${cells}</tr>`;
    })
    .join("\n");

  return `<table>\n<thead><tr>${thead}</tr></thead>\n<tbody>\n${tbody}\n</tbody>\n</table>`;
}

export function markdownToHtml(md: string): string {
  const lines = md.split("\n");
  const output: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Headings
    const h1 = line.match(/^# (.+)$/);
    const h2 = line.match(/^## (.+)$/);
    const h3 = line.match(/^### (.+)$/);
    if (h1) { output.push(`<h1>${parseInline(h1[1])}</h1>`); i++; continue; }
    if (h2) { output.push(`<h2>${parseInline(h2[1])}</h2>`); i++; continue; }
    if (h3) { output.push(`<h3>${parseInline(h3[1])}</h3>`); i++; continue; }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) { output.push("<hr>"); i++; continue; }

    // Blockquote
    if (line.startsWith("> ")) {
      const content = line.slice(2);
      output.push(`<blockquote>${parseInline(content)}</blockquote>`);
      i++;
      continue;
    }

    // Table: collect consecutive table lines
    if (line.startsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        tableLines.push(lines[i]);
        i++;
      }
      output.push(parseTable(tableLines));
      continue;
    }

    // Empty line
    if (line.trim() === "") { output.push(""); i++; continue; }

    // Paragraph
    output.push(`<p>${parseInline(line)}</p>`);
    i++;
  }

  return output.join("\n");
}
