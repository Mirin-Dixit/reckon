const $ = id => document.getElementById(id);
const make = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined)
        node.textContent = text;
    if (className)
        node.className = className;
    return node;
};
let session, packet, batch = 1, index = 0, evidence = [], source, dirty = false;
let searchTerms = [], busy = false;
const row = () => packet.records[index];
const message = (text, error = false) => {
    $("message").textContent = text;
    $("message").classList.toggle("error", error);
};
const labels = {
    answerable: "Answerable", off_topic: "Off topic",
    temporal_near_miss: "Temporal near-miss · version / time",
    entity_near_miss: "Entity near-miss · different entity",
    attribute_near_miss: "Attribute near-miss · missing attribute",
    false_premise: "False premise", ambiguous_question: "Ambiguous · needs clarification",
    source: "Source version and provenance", split: "Topic/split overlap and related questions",
    answerability: "Corpus-wide answerability", evidence: "Exact evidence and semantic support",
    reference_answer: "Every claim in the reference answer", negative_absence: "Missing facts across the full corpus",
    ambiguity: "Competing interpretations", compound: "Every required premise",
};
const explanations = {
    answerable: "The corpus supports a complete answer to the exact question.",
    off_topic: "The requested subject is outside this corpus, such as an unrelated product.",
    temporal_near_miss: "The missing facts concern a different time or version. Check the requested version explicitly.",
    entity_near_miss: "A related entity is documented, but the requested entity's facts are missing.",
    attribute_near_miss: "The entity exists, but the requested property or guarantee is not supported.",
    false_premise: "A premise is unsupported and the requested facts cannot be supplied. A fully supported correction can still be answerable.",
    ambiguous_question: "Different plausible meanings need clarification before a complete answer can be given.",
};
async function api(path, method = "GET", body) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
        const response = await fetch(path, {
            method, credentials: "omit", cache: "no-store", redirect: "error",
            signal: controller.signal,
            headers: { "Content-Type": "application/json", "X-Review-Token": session?.token || "" },
            body: body === undefined ? undefined : JSON.stringify(body),
        });
        const payload = await response.json();
        if (!response.ok)
            throw new Error(Array.isArray(payload.detail) ? payload.detail.join("; ") : payload.detail || "Request failed");
        return payload;
    }
    finally {
        clearTimeout(timer);
    }
}
async function run(action) {
    if (busy)
        return;
    busy = true;
    document.querySelectorAll("button, input, select, textarea").forEach(control => {
        if (!control.readOnly) {
            control.dataset.wasDisabled = control.disabled;
            control.disabled = true;
        }
    });
    try {
        await action();
    }
    catch (error) {
        message(error.name === "AbortError" ? "Request timed out. Reload to check whether the save completed." : error.message || "Could not reach the local review service.", true);
    }
    finally {
        busy = false;
        document.querySelectorAll("button, input, select, textarea").forEach(control => {
            if (!control.readOnly)
                control.disabled = control.dataset.wasDisabled === "true";
        });
        if (packet && row().assisted)
            document.querySelector('input[name="basis"][value="independent"]').disabled = true;
        navigation();
    }
}
function options(id, values) {
    const select = $(id);
    select.replaceChildren(make("option", "Choose…"));
    select.firstChild.value = "";
    values.forEach(value => { const option = make("option", labels[value] || value); option.value = value; select.append(option); });
}
function canLeave() { return !(dirty || $("passage-finding").value.trim()) || confirm("Unsaved changes will be lost. Continue without saving?"); }
function navigation() {
    if (!packet)
        return;
    $("previous").disabled = index === 0 || busy;
    $("next").disabled = index === packet.records.length - 1 || busy;
    $("reveal").disabled = packet.revealed || packet.first_pass_saved !== 10 || busy;
    $("validate").disabled = !packet.revealed || busy;
    $("packet").disabled = busy;
}
async function loadPacket(number) {
    packet = await api(`/api/packets/${number}`);
    batch = number;
    index = Math.max(0, packet.records.findIndex(r => packet.revealed ? !r.final_saved : !r.first_pass_saved));
    $("validation-panel").hidden = true;
    searchTerms = [];
    $("search-results").replaceChildren();
    $("passage-finding").value = "";
    render();
    message("Loaded your saved draft. Proposed labels stay hidden until the packet's first pass is complete.");
}
function renderEvidence() {
    $("evidence-count").textContent = `(${evidence.length})`;
    $("evidence-list").replaceChildren();
    evidence.forEach((span, i) => {
        const box = make("div", undefined, "passage");
        box.append(make("p", `${span.doc_id} · [${span.start_char}, ${span.end_char})`, "small"), make("pre", span.text), make("p", span.finding));
        const remove = make("button", "Remove passage");
        remove.type = "button";
        remove.onclick = () => { evidence.splice(i, 1); dirty = true; renderEvidence(); };
        box.append(remove);
        $("evidence-list").append(box);
    });
}
function renderAnnotation() {
    const current = row(), proposed = current.annotation;
    $("locked-first").textContent = JSON.stringify(Object.fromEntries(["first_pass_decision", "first_pass_category", "first_pass_findings", "corpus_search_notes", "independent_first_pass"].map(k => [k, current.submission[k]])), null, 2);
    const panel = $("annotation");
    panel.replaceChildren();
    for (const [title, value] of [
        ["Proposed decision / category", `${proposed.expected_decision} / ${proposed.category}`],
        ["Reference answer", proposed.expected_answer], ["Expected safe behavior", proposed.expected_safe_behavior],
        ["Absence rationale", proposed.absence_note], ["Interpretations", proposed.ambiguity_interpretations.join("\n")],
        ["Missing premises", proposed.compound_missing_premises.join("\n")], ["Author notes", proposed.notes],
    ])
        if (value) {
            panel.append(make("h3", title), make("p", value));
        }
    [...proposed.evidence_spans, ...proposed.diagnostic_spans].forEach(span => {
        const box = make("div", undefined, "passage");
        const button = make("button", "Locate in full source");
        button.type = "button";
        button.onclick = () => run(() => openSource(span.doc_id, null, span));
        box.append(make("p", `${span.id} · Unicode [${span.start_char}, ${span.end_char})`, "small"), make("pre", span.text), button);
        panel.append(box);
    });
    const details = make("details"), pre = make("pre", JSON.stringify(proposed, null, 2));
    details.append(make("summary", "Full proposed annotation, ownership and parent links"), pre);
    panel.append(details);
    $("checks").replaceChildren();
    current.required_checks.forEach(check => {
        const label = make("label", undefined, "choice"), input = make("input");
        input.type = "checkbox";
        input.value = check;
        input.name = "review-check";
        input.checked = current.submission.checks.includes(check);
        label.append(input, document.createTextNode(labels[check] || check));
        $("checks").append(label);
    });
    $("action").value = current.submission.action || "";
    $("rationale").value = current.submission.rationale;
    $("proposal").value = current.submission.proposed_changes ? JSON.stringify(current.submission.proposed_changes, null, 2) : "";
    const validation = current.validation;
    $("row-validation").textContent = validation ? `${validation.status}: ${validation.issues?.join("; ") || "Valid receipt only. Not imported or benchmark-accepted."}` : "Not yet validated.";
    $("row-validation").classList.toggle("error", !!validation && validation.status !== "validated_not_imported");
}
function render() {
    const current = row(), saved = current.submission;
    $("progress").textContent = `First pass ${packet.first_pass_saved}/10 · ${10 - packet.first_pass_saved} remaining`;
    $("validation-progress").textContent = `Annotation reviews ${packet.final_saved}/10 · validated, not imported ${packet.validated_not_imported}/10 · benchmark acceptance unchanged`;
    $("position").textContent = `Question ${index + 1} / 10`;
    $("candidate").textContent = `PACKET ${String(batch).padStart(2, "0")} / ${saved.candidate_id}`;
    $("question-title").textContent = current.question;
    $("phase").textContent = packet.revealed ? "Annotation review · your first-pass judgment is locked" : `First pass · ${current.first_pass_saved ? "saved" : "not saved"}`;
    $("first-form").hidden = packet.revealed;
    $("annotation-panel").hidden = !packet.revealed;
    $("decision").value = saved.first_pass_decision || "";
    $("category").value = saved.first_pass_category || "";
    $("findings").value = saved.first_pass_findings;
    $("search-notes").value = saved.corpus_search_notes;
    document.querySelectorAll('input[name="basis"]').forEach(input => {
        input.checked = current.first_pass_saved && input.value === (current.assisted ? "assisted" : "independent");
        input.disabled = current.assisted && input.value === "independent";
    });
    evidence = structuredClone(saved.evidence_records);
    renderEvidence();
    if (packet.revealed)
        renderAnnotation();
    $("export").href = `/api/packets/${batch}/export`;
    $("export").removeAttribute("aria-disabled");
    $("import-panel").hidden = packet.revealed || packet.first_pass_saved > 0;
    dirty = false;
    navigation();
}
$("first-form").onsubmit = event => {
    event.preventDefault();
    run(async () => {
        if ($("passage-finding").value.trim())
            throw new Error("Add the selected passage to your evidence, or clear its finding, before saving.");
        packet = await api(`/api/packets/${batch}/first-pass/${row().submission.candidate_id}`, "PUT", {
            revision: packet.revision, first_pass_decision: $("decision").value,
            first_pass_category: $("category").value, first_pass_findings: $("findings").value,
            corpus_search_notes: $("search-notes").value,
            basis: document.querySelector('input[name="basis"]:checked').value,
            evidence_records: evidence,
        });
        render();
        message("First-pass judgment saved. Nothing was accepted or imported.");
    });
};
$("final-form").onsubmit = event => {
    event.preventDefault();
    run(async () => {
        if ($("passage-finding").value.trim())
            throw new Error("Add the selected passage to your evidence, or clear its finding, before saving.");
        const proposal = $("proposal").value.trim();
        let parsed = null;
        if (proposal) {
            try {
                parsed = JSON.parse(proposal);
            }
            catch {
                throw new Error("Proposed changes must be a valid JSON object.");
            }
        }
        packet = await api(`/api/packets/${batch}/annotation/${row().submission.candidate_id}`, "PUT", {
            revision: packet.revision, action: $("action").value, rationale: $("rationale").value,
            checks: [...document.querySelectorAll('input[name="review-check"]:checked')].map(c => c.value),
            proposed_changes: parsed, evidence_records: evidence,
        });
        render();
        message(`Annotation review saved: ${row().validation.status}. The benchmark ledger is unchanged.`);
    });
};
$("reveal").onclick = () => run(async () => {
    if (!canLeave() || !confirm("Reveal proposed annotations for this packet? Your ten first-pass entries will be locked permanently in this workspace."))
        return;
    packet = await api(`/api/packets/${batch}/reveal`, "POST", { revision: packet.revision });
    index = 0;
    render();
    message("Proposed annotations revealed. Compare each claim with the pinned sources.");
});
$("validate").onclick = () => run(async () => {
    if (dirty)
        throw new Error("Save your changes before validating.");
    const result = await api(`/api/packets/${batch}/validate`, "POST", { revision: packet.revision });
    $("validation-results").textContent = JSON.stringify(result, null, 2);
    $("validation-panel").hidden = false;
    $("validation-panel").open = true;
    message(`${result.status}. Validation never imports reviews or freezes Test.`);
});
$("import").onclick = () => run(async () => {
    const file = $("import-file").files[0];
    if (!file || file.size > 512 * 1024)
        throw new Error("Choose a reviewer JSON file smaller than 512 KiB.");
    if (!canLeave())
        return;
    const content = JSON.parse(await file.text());
    packet = await api(`/api/packets/${batch}/import-notes`, "POST", { revision: packet.revision, records: Array.isArray(content) ? content : [content] });
    index = Math.max(0, packet.records.findIndex(r => !r.first_pass_saved));
    render();
    message("Imported first-pass notes as assisted. Originals are unchanged; no independent attestation was imported.");
});
$("packet").onchange = () => {
    if (!canLeave()) {
        $("packet").value = batch;
        return;
    }
    run(() => loadPacket(Number($("packet").value)));
};
for (const [id, step] of [["previous", -1], ["next", 1]])
    $(id).onclick = () => {
        if (!canLeave())
            return;
        index += step;
        searchTerms = [];
        $("search-results").replaceChildren();
        $("passage-finding").value = "";
        render();
        $("question-title").focus();
    };
$("export").onclick = event => { if (dirty) {
    event.preventDefault();
    message("Save your changes before exporting.", true);
} };
for (const id of ["first-form", "final-form"])
    $(id).addEventListener("input", () => { dirty = true; });
window.addEventListener("beforeunload", event => { if (dirty) {
    event.preventDefault();
    event.returnValue = "";
} });
async function openSource(id, line = null, span = null) {
    source = await api(`/api/sources/${encodeURIComponent(id)}`);
    $("source-select").value = id;
    $("source-text").value = source.text;
    $("source-info").textContent = `${id} · Python ${source.version} · exact pinned text`;
    const start = span ? Array.from(source.text).slice(0, span.start_char).join("").length : line ? source.text.split("\n").slice(0, line - 1).join("\n").length + (line > 1 ? 1 : 0) : 0;
    const end = span ? Array.from(source.text).slice(0, span.end_char).join("").length : line ? start + source.text.slice(start).split("\n")[0].length : start;
    $("source-text").focus();
    $("source-text").setSelectionRange(start, end);
    $("source-text").scrollTop = Math.max(0, (source.text.slice(0, start).split("\n").length - 4) * 21.45);
    showCoordinates();
}
$("source-select").onchange = () => { if ($("source-select").value)
    run(() => openSource($("source-select").value)); };
$("search-form").onsubmit = event => {
    event.preventDefault();
    run(async () => {
        const term = $("search").value.trim();
        const result = await api(`/api/search?q=${encodeURIComponent(term)}`);
        searchTerms.push(term);
        $("search-results").replaceChildren(make("p", `${result.total} matching lines across ${result.documents_searched} documents${result.truncated ? " · first 200 shown" : ""}.`, "small"));
        result.matches.forEach(hit => {
            const button = make("button", `${hit.doc_id}:${hit.line} — ${hit.text}`);
            button.type = "button";
            button.onclick = () => run(() => openSource(hit.doc_id, hit.line));
            $("search-results").append(button);
        });
        const note = make("p", `Searches you ran for this question: ${searchTerms.join(", ")}. Record what you actually checked in your search notes.`, "small");
        $("search-results").append(note);
    });
};
function selection() {
    const area = $("source-text");
    return { start_char: Array.from(area.value.slice(0, area.selectionStart)).length, end_char: Array.from(area.value.slice(0, area.selectionEnd)).length };
}
function showCoordinates() {
    const position = selection();
    $("coordinates").textContent = `Unicode [${position.start_char}, ${position.end_char}) · line ${$("source-text").value.slice(0, $("source-text").selectionStart).split("\n").length}`;
}
$("source-text").addEventListener("select", showCoordinates);
$("add-passage").onclick = () => run(async () => {
    const position = selection();
    if (!source || position.start_char === position.end_char)
        throw new Error("Select source text first.");
    if (!$("passage-finding").value.trim())
        throw new Error("Explain what this passage establishes first.");
    const span = await api("/api/evidence", "POST", { doc_id: source.id, ...position, finding: $("passage-finding").value });
    if (evidence.some(s => s.id === span.id))
        throw new Error("That passage is already recorded. Remove it before replacing its finding.");
    evidence.push(span);
    dirty = true;
    $("passage-finding").value = "";
    renderEvidence();
    message("Passage added to this question. Save your judgment to keep it.");
});
run(async () => {
    session = await api("/api/session");
    $("identity").textContent = `Reviewer: ${session.reviewer_id} · ${session.profile || "full-160"} · one local reviewer workspace`;
    for (const number of session.packets) {
        const option = make("option", `Packet ${number}`);
        option.value = number;
        $("packet").append(option);
    }
    for (const [id, field] of [["decision", "first_pass_decision"], ["category", "first_pass_category"], ["action", "action"]])
        options(id, session.schema.properties[field].enum);
    session.schema.properties.first_pass_category.enum.forEach(category => {
        $("category-help").append(make("p", `${labels[category] || category}: ${explanations[category] || category}`, "small"));
    });
    $("source-select").append(make("option", "Choose a document…"));
    $("source-select").firstChild.value = "";
    session.sources.forEach(doc => {
        const option = make("option", doc.filename);
        option.value = doc.id;
        $("source-select").append(option);
    });
    await loadPacket(1);
});
