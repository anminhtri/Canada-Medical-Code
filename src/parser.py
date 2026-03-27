import json
import re
from typing import Any


def is_garbage(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.isdigit():
        return True
    if "SECTION 1" in stripped:
        return True
    if "CANADIAN CLASSIFICATION OF HEALTH INTERVENTIONS" in stripped:
        return True
    if "Tabular List of" in stripped:
        return True
    if "Therapeutic Interventions on" in stripped:
        return True
    if "Attribute Reference Number" in stripped:
        return True
    if "Attribute Optional or" in stripped:
        return True
    if stripped.startswith("S ") and "Optional" in stripped:
        return True
    return "Attribute Reference Description" in stripped


def parse_pdf_data(pages_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    cci_pattern = r"^\s*(\d+\.[A-Z]{2}\.\d{2})\.\^\^\s*(.*?)(?:\s+(S\s+\d+|L\s+\d+|E\s+\d+))?\s*$"
    qualifier_pattern = r"^\s*(\d+\.[A-Z]{2}\.\d{2}\.[A-Za-z0-9\-]+)\s+(.*?)\s*$"

    all_text = ""
    all_tables: list[list[list[str | None]]] = []

    for page in pages_data:
        text: str = page.get("text", "")
        extracted_lines = [txt_line for txt_line in text.split("\n") if not is_garbage(txt_line)]
        all_text += "\n".join(extracted_lines) + "\n"
        if page.get("tables"):
            all_tables.extend(page["tables"])

    lines = all_text.split("\n")

    current_entry: dict[str, Any] | None = None
    in_qualifiers: bool = False
    current_section: str | None = None

    for line in lines:
        if not line.strip():
            continue

        cci_match = re.match(cci_pattern, line)
        if cci_match:
            code = cci_match.group(1)

            existing = next((e for e in entries if e["code"] == code), None)
            if existing:
                current_entry = existing
                current_section = None
                in_qualifiers = False
                continue

            desc = cci_match.group(2).strip()

            current_entry = {
                "code": code,
                "description": desc,
                "note": [],
                "code_also": [],
                "includes": [],
                "excludes": [],
                "omit_code": [],
                "attributes": {
                    "S": {"type": "N/A", "codes": []},
                    "L": {"type": "N/A", "codes": []},
                    "E": {"type": "N/A", "codes": []},
                },
                "qualifiers": [],
            }

            attr_flag = cci_match.group(3)
            if attr_flag:
                for attr_type in ["S", "L", "E"]:
                    if attr_flag.startswith(attr_type):
                        current_entry["attributes"][attr_type]["codes"].append(
                            attr_flag.replace(" ", "")
                        )
                        current_entry["attributes"][attr_type]["type"] = "Optional"

            entries.append(current_entry)
            in_qualifiers = False
            current_section = None
            continue

        if not current_entry:
            continue

        q_match = re.match(qualifier_pattern, line)
        if q_match:
            in_qualifiers = True
            current_section = "qualifiers_linear"
            q_code = q_match.group(1)
            q_desc = q_match.group(2).strip()

            if not any(q["code"] == q_code for q in current_entry["qualifiers"]):
                current_entry["qualifiers"].append(
                    {
                        "code": q_code,
                        "approach": "N/A",
                        "description": q_desc,
                        "includes": [],
                    }
                )
            continue

        sec_match = re.search(
            r"^\s*(Note|Includes|Excludes|Code Also|Omit Code):\s*(.*)",
            line,
            re.IGNORECASE,
        )
        if sec_match:
            sec_name = sec_match.group(1).lower().replace(" ", "_")
            content = sec_match.group(2).strip()

            if in_qualifiers:
                if sec_name == "includes" and len(current_entry["qualifiers"]) > 0:
                    if content:
                        current_entry["qualifiers"][-1]["includes"].append(content)
                    current_section = "qualifiers_linear"
                else:
                    current_section = None
            else:
                current_section = sec_name
                if content:
                    current_entry[sec_name].append(content)
            continue

        stripped = line.strip()

        if in_qualifiers and current_section == "qualifiers_linear":
            if len(current_entry["qualifiers"]) > 0 and len(current_entry["qualifiers"][-1]["includes"]) > 0:
                current_entry["qualifiers"][-1]["includes"][-1] += " " + stripped
        elif current_section and not in_qualifiers:
            if (
                re.search(r"^\s*\d+\.[A-Z]{2}\.\d{2}\.[A-Za-z0-9\-]+", stripped)
                or "percutaneous" in stripped
                or re.search(
                    r"using (antithrombotic|thrombolytic)", stripped, re.IGNORECASE
                )
            ):
                continue
            
            key: str = current_section
            current_entry[key].append(stripped)

    for t in all_tables:
        if not t or not t[0] or not t[0][0]:
            continue
        header = t[0][0].replace("\n", " ")
        cci_match = re.search(r"(\d+\.[A-Z]{2}\.\d{2})", header)
        if cci_match:
            code = cci_match.group(1)
            entry = next((e for e in entries if e["code"] == code), None)
            if entry:
                approaches = [
                    a.replace("\n", " ").strip() if a else "N/A" for a in t[0][1:]
                ]
                for r_idx in range(1, len(t)):
                    row = t[r_idx]
                    if not row or not row[0]:
                        continue
                    desc = row[0].replace("\n", " ").strip()
                    for c_idx in range(1, len(row)):
                        cell = row[c_idx]
                        if not cell:
                            continue
                        cell_lines = [cl.strip() for cl in cell.split("\n") if cl.strip()]
                        if not cell_lines:
                            continue
                        q_code = cell_lines[0]
                        if not re.match(
                            r"^\d+\.[A-Z]{2}\.\d{2}\.[A-Za-z0-9\-]+$", q_code
                        ):
                            continue

                        entry["qualifiers"] = [
                            q for q in entry["qualifiers"] if q["code"] != q_code
                        ]

                        includes: list[str] = []
                        is_includes = False
                        for c_line in cell_lines[1:]:
                            if c_line.lower().startswith("includes:"):
                                is_includes = True
                                continue
                            if is_includes:
                                clean_line = c_line.lstrip("•*- â€¢").strip()
                                clean_line = clean_line.replace("\u00e2\u20ac\u00a2", "")
                                if clean_line:
                                    includes.append(clean_line)

                        app = (
                            approaches[c_idx - 1]
                            if c_idx - 1 < len(approaches)
                            else "N/A"
                        )
                        full_desc = f"{desc} using {app}" if app != "N/A" else desc

                        entry["qualifiers"].append(
                            {
                                "code": q_code,
                                "approach": app,
                                "description": full_desc,
                                "includes": includes,
                            }
                        )

    for entry in entries:
        for sec in ["includes", "excludes", "note", "code_also"]:
            cleaned: list[str] = []
            for item in entry[sec]:
                if re.match(r"^\s*\d+\.[A-Z]{2}\.\d{2}\.\^\^", item):
                    continue
                if re.search(
                    r"using (antithrombotic|thrombolytic)", item, re.IGNORECASE
                ):
                    continue
                if re.search(
                    r"using (antiinfective|antineoplastic)", item, re.IGNORECASE
                ):
                    continue
                if re.search(r"using other pharmacological", item, re.IGNORECASE):
                    continue
                if "percutaneous" in item and "approach" in item:
                    continue
                if re.search(r"\d+\.[A-Z]{2}\.\d{2}\.[A-Z0-9\-]+", item):
                    continue
                if item.strip() == "Includes:":
                    continue
                if item.strip().startswith(("•", "â€¢", "\u00e2\u20ac\u00a2")):
                    continue
                item = item.replace("â€¢", "").replace("\u00e2\u20ac\u00a2", "").strip()
                leak_keywords = [
                    "retaplase",
                    "tenecteplase",
                    "dipyridamole",
                    "(tPA)",
                    "tissue plasminogen activator",
                    "warfarin, heparin",
                    "anistreplase, alteplase",
                ]
                if any(kw in item for kw in leak_keywords):
                    continue
                cleaned.append(item)
            entry[sec] = cleaned

    return entries


if __name__ == "__main__":

    with open("cache/raw_text_68_69.json", encoding="utf-8") as file:
        pages_data = json.load(file)
    res = parse_pdf_data(pages_data)
    with open("CCICodeExample(68-69)_output.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"Generated {len(res)} entries.")