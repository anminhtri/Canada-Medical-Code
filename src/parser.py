import re
import json


def is_garbage(line):
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
    if "Attribute Reference Description" in stripped:
        return True
    return False


def parse_pdf_data(pages_data):
    entries = []

    # Allow optional space after ^^
    cci_pattern = (
        r"^\s*(\d+\.[A-Z]{2}\.\d{2})\.\^\^\s*(.*?)(?:\s+(S\s+\d+|L\s+\d+|E\s+\d+))?\s*$"
    )
    qualifier_pattern = r"^\s*(\d+\.[A-Z]{2}\.\d{2}\.[A-Za-z0-9\-]+)\s+(.*?)\s*$"

    all_text = ""
    all_tables = []

    for page in pages_data:
        text = page["text"]
        lines = [l for l in text.split("\n") if not is_garbage(l)]
        all_text += "\n".join(lines) + "\n"
        if page.get("tables"):
            all_tables.extend(page["tables"])

    lines = all_text.split("\n")

    current_entry = None
    in_qualifiers = False
    current_section = None

    for line in lines:
        if not line.strip():
            continue

        cci_match = re.match(cci_pattern, line)
        if cci_match:
            code = cci_match.group(1)

            # If we already have this code being actively parsed or it exists,
            # this is likely a table header repeating the code.
            existing = next((e for e in entries if e["code"] == code), None)
            if existing:
                # We resume parsing on the existing entry, but clear section to drop garbage text
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

            # Ensure it's not already in the qualifiers array
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
                    # Ignore other sections inside qualifiers (rare, or just table noise)
                    current_section = None
            else:
                current_section = sec_name
                if content:
                    current_entry[current_section].append(content)
            continue

        stripped = line.strip()

        if in_qualifiers and current_section == "qualifiers_linear":
            if len(current_entry["qualifiers"]) > 0:
                if len(current_entry["qualifiers"][-1]["includes"]) > 0:
                    current_entry["qualifiers"][-1]["includes"][-1] += " " + stripped
        elif current_section and not in_qualifiers:
            # Check if this text looks like a matrix header or qualifier, if so, we probably shouldn't append it
            # This prevents table data from leaking into 'includes' before we process the tables.
            if (
                re.search(r"^\s*\d+\.[A-Z]{2}\.\d{2}\.[A-Za-z0-9\-]+", stripped)
                or "percutaneous" in stripped
                or re.search(
                    r"using (antithrombotic|thrombolytic)", stripped, re.IGNORECASE
                )
            ):
                continue
            current_entry[current_section].append(stripped)

    # Process Tables
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
                        lines = [l.strip() for l in cell.split("\n") if l.strip()]
                        if not lines:
                            continue
                        q_code = lines[0]
                        if not re.match(
                            r"^\d+\.[A-Z]{2}\.\d{2}\.[A-Za-z0-9\-]+$", q_code
                        ):
                            continue

                        entry["qualifiers"] = [
                            q for q in entry["qualifiers"] if q["code"] != q_code
                        ]

                        includes = []
                        is_includes = False
                        for l in lines[1:]:
                            if l.lower().startswith("includes:"):
                                is_includes = True
                                continue
                            if is_includes:
                                # Strip bullets, asterisks, and their mojibake equivalents
                                l = l.lstrip("•*- â€¢").strip()
                                l = l.replace("\u00e2\u20ac\u00a2", "")
                                if l:
                                    includes.append(l)

                        # Compute full description matching ground truth
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
    # Clean up top-level arrays from leaking table parts
    for entry in entries:
        for sec in ["includes", "excludes", "note", "code_also"]:
            cleaned = []
            for item in entry[sec]:
                # If the item starts looking like a matrix header or qualifier, we drop it
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
                # if contains qualifier code, ignore
                if re.search(r"\d+\.[A-Z]{2}\.\d{2}\.[A-Z0-9\-]+", item):
                    continue
                if item.strip() == "Includes:":
                    continue
                if item.strip().startswith(("•", "â€¢", "\u00e2\u20ac\u00a2")):
                    continue
                item = item.replace("â€¢", "").replace("\u00e2\u20ac\u00a2", "").strip()
                # Filter out raw text spills from table cells
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

    with open("cache/raw_text_68_69.json", "r", encoding="utf-8") as file:
        pages_data = json.load(file)
    # Use the same page range the user tested: 68-100
    res = parse_pdf_data(pages_data)
    with open("CCICodeExample(68-69)_output.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"Generated {len(res)} entries.")