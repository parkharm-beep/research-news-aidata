import fs from "fs";
import path from "path";
import { markdownToHtml } from "./markdown";

export default function Home() {
  const indexPath = path.join(process.cwd(), "..", "index.md");
  const content = fs.readFileSync(indexPath, "utf-8");
  const html = markdownToHtml(content);

  return (
    <main dangerouslySetInnerHTML={{ __html: html }} />
  );
}
