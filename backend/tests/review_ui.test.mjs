// DOM contract tests with mocked transport; not a replacement for browser QA.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import vm from "node:vm";
const html = await readFile(new URL("../app/evaluation/review_ui/index.html", import.meta.url), "utf8");
const script = await readFile(new URL("../app/evaluation/review_ui/review.js", import.meta.url), "utf8");
const drain = () => new Promise(resolve => setImmediate(resolve));
async function ui({ confirm = () => true, failSave = false, assistedImport = false, profile = "full-160" } = {}) {
    const nodes = [], ids = new Map(), requests = [];
    class Element {
        constructor(tag) {
            this.tagName = tag;
            this.children = [];
            this.textContent = "";
            this.value = "";
            this.disabled = false;
            this.hidden = false;
            this.checked = false;
            this.dataset = {};
            this.selectionStart = 0;
            this.selectionEnd = 0;
            this.listeners = {};
            this.classList = { toggle() { } };
            nodes.push(this);
        }
        append(...children) { this.children.push(...children); }
        replaceChildren(...children) { this.children = [...children]; }
        get firstChild() { return this.children[0]; }
        removeAttribute(name) { delete this[name]; }
        addEventListener(name, callback) { this.listeners[name] = callback; }
        focus() { document.activeElement = this; }
        setSelectionRange(start, end) { this.selectionStart = start; this.selectionEnd = end; }
    }
    for (const match of html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) {
        const node = new Element(match[1]);
        node.hidden = /\bhidden\b/.test(match[2]);
        node.disabled = /\bdisabled\b/.test(match[2]);
        node.readOnly = /\breadonly\b/.test(match[2]);
        ids.set(match[3], node);
    }
    const basis = ["independent", "assisted"].map(value => {
        const input = new Element("input");
        input.name = "basis";
        input.value = value;
        return input;
    });
    const document = {
        getElementById: id => { assert.ok(ids.has(id), `Unknown DOM ID ${id}`); return ids.get(id); },
        createElement: tag => new Element(tag),
        createTextNode: text => ({ textContent: text }),
        querySelectorAll: selector => selector === "button, input, select, textarea" ? nodes.filter(n => ["button", "input", "select", "textarea"].includes(n.tagName))
            : selector === "button" ? nodes.filter(n => n.tagName === "button")
                : selector.includes('name="basis"') ? basis
                    : nodes.filter(n => n.name === "review-check" && (!selector.includes(":checked") || n.checked)),
        querySelector: selector => selector.includes('value="independent"') ? basis[0] : basis.find(n => n.checked),
    };
    const record = id => ({
        question: `Original blind question ${id}`, assisted: false, first_pass_saved: false,
        final_saved: false, validation: null,
        submission: { candidate_id: id, first_pass_decision: null, first_pass_category: null,
            first_pass_findings: "", corpus_search_notes: "", independent_first_pass: null,
            evidence_records: [], checks: [], action: null, rationale: "", proposed_changes: null },
    });
    let state = { revision: 0, revealed: false, records: [record("q-1"), record("q-2")],
        first_pass_saved: 0, final_saved: 0, validated_not_imported: 0 };
    const session = { reviewer_id: "fixture-only", token: "fixture-token", profile, packets: profile === "full-160" ? [1, 2] : [1, 2, 3],
        schema: { properties: {
                first_pass_decision: { enum: ["ANSWER", "ABSTAIN", "CLARIFY"] },
                first_pass_category: { enum: ["answerable", "temporal_near_miss"] },
                action: { enum: ["accept", "revise", "reject", "reclassify"] },
            } }, sources: [{ id: "fixture-doc", filename: "fixture.rst" }] };
    const sourceText = "A😀e\u0301Z\nUntrusted <script>source</script>";
    const fetch = async (path, options) => {
        const body = options.body ? JSON.parse(options.body) : undefined;
        requests.push({ path, ...options, body });
        let status = 200, payload;
        if (path === "/api/session")
            payload = session;
        else if (path.startsWith("/api/sources/"))
            payload = { id: "fixture-doc", version: "3.11.9", text: sourceText };
        else if (path.startsWith("/api/search"))
            payload = { total: 1, documents_searched: 34,
                matches: [{ doc_id: "fixture-doc", line: 2, text: "<img src=x onerror=alert(1)>" }], truncated: false };
        else if (path === "/api/evidence")
            payload = { ...body,
                id: `fixture-doc_s${body.start_char}_${body.end_char}`,
                text: Array.from(sourceText).slice(body.start_char, body.end_char).join("") };
        else if (path.endsWith("/import-notes")) {
            state.records[0].assisted = assistedImport;
            state.records[0].first_pass_saved = true;
            state.records[0].submission.first_pass_findings = "Imported assisted fixture";
            state.first_pass_saved = 1;
            state.revision++;
            payload = state;
        }
        else if (options.method === "PUT") {
            if (failSave) {
                status = 503;
                payload = { detail: "Save failed; previous draft preserved" };
            }
            else {
                const target = state.records.find(r => path.endsWith(r.submission.candidate_id));
                Object.assign(target.submission, body);
                target.first_pass_saved = true;
                target.assisted = body.basis === "assisted";
                target.submission.independent_first_pass = target.assisted ? null : true;
                state.first_pass_saved++;
                state.revision++;
                payload = state;
            }
        }
        else
            payload = state;
        return { ok: status === 200, json: async () => structuredClone(payload) };
    };
    const context = vm.createContext({ document, fetch, setTimeout, clearTimeout,
        AbortController, structuredClone, confirm, window: { addEventListener() { } } });
    vm.runInContext(script, context, { filename: "review.js" });
    await drain();
    return { ids, requests, basis, nodes, sourceText, event: { preventDefault() { } } };
}
test("blind startup has schema choices, no defaults, and no annotation panel", async () => {
    const { ids, requests } = await ui();
    assert.equal(ids.get("decision").value, "");
    assert.equal(ids.get("category").value, "");
    assert.equal(ids.get("annotation-panel").hidden, true);
    assert.equal(ids.get("reveal").disabled, true);
    assert.equal(ids.get("question-title").textContent, "Original blind question q-1");
    assert.deepEqual(ids.get("decision").children.map(c => c.value), ["", "ANSWER", "ABSTAIN", "CLARIFY"]);
    assert.ok(requests.every(r => r.method === "GET"));
});
test("pilot uses the existing page with a visible profile and three packets", async () => {
    const { ids } = await ui({ profile: "python311-pilot30.v1" });
    assert.match(ids.get("identity").textContent, /python311-pilot30\.v1/);
    assert.equal(ids.get("packet").children.length, 3);
    assert.equal(ids.get("decision").value, "");
    assert.equal(ids.get("annotation-panel").hidden, true);
});
test("save sends only explicit first-pass choices and retains assisted basis", async () => {
    const { ids, basis, requests, event } = await ui();
    ids.get("decision").value = "ABSTAIN";
    ids.get("category").value = "temporal_near_miss";
    ids.get("findings").value = "My fixture findings";
    ids.get("search-notes").value = "Actual fixture searches";
    basis[1].checked = true;
    ids.get("first-form").onsubmit(event);
    await drain();
    const saved = requests.find(r => r.method === "PUT");
    assert.equal(saved.body.basis, "assisted");
    assert.equal(saved.body.first_pass_findings, "My fixture findings");
    assert.equal(Object.hasOwn(saved.body, "independent_first_pass"), false);
    assert.equal(basis[0].disabled, true);
    assert.match(ids.get("message").textContent, /saved/);
});
test("save failure retains entered findings and does not advance the question", async () => {
    const { ids, basis, event } = await ui({ failSave: true });
    ids.get("findings").value = "Do not lose this fixture text";
    ids.get("decision").value = "ABSTAIN";
    ids.get("category").value = "temporal_near_miss";
    ids.get("search-notes").value = "Fixture searches";
    basis[1].checked = true;
    ids.get("first-form").onsubmit(event);
    await drain();
    assert.equal(ids.get("findings").value, "Do not lose this fixture text");
    assert.equal(ids.get("question-title").textContent, "Original blind question q-1");
    assert.match(ids.get("message").textContent, /Save failed/);
});
test("unsaved navigation can be cancelled", async () => {
    const { ids } = await ui({ confirm: () => false });
    ids.get("first-form").listeners.input();
    ids.get("next").onclick();
    assert.equal(ids.get("question-title").textContent, "Original blind question q-1");
});
test("passage selection converts UTF-16 selection to exact Unicode code points", async () => {
    const { ids, requests } = await ui();
    ids.get("source-select").value = "fixture-doc";
    ids.get("source-select").onchange();
    await drain();
    ids.get("source-text").setSelectionRange(1, 5);
    ids.get("passage-finding").value = "Synthetic Unicode finding";
    ids.get("add-passage").onclick();
    await drain();
    const request = requests.find(r => r.path === "/api/evidence");
    assert.equal(request.body.start_char, 1);
    assert.equal(request.body.end_char, 4);
    assert.equal(ids.get("evidence-count").textContent, "(1)");
});
test("source search is explicit and untrusted matches render as text", async () => {
    const { ids, nodes, requests, event } = await ui();
    assert.ok(!requests.some(r => r.path.startsWith("/api/search")));
    ids.get("search").value = "fixture";
    ids.get("search-form").onsubmit(event);
    await drain();
    assert.ok(nodes.some(n => n.tagName === "button" && n.textContent.includes("<img src=x onerror=alert(1)>")));
    assert.ok(!nodes.some(n => n.tagName === "img"));
    assert.match(ids.get("search-results").children[0].textContent, /34 documents/);
});
test("imported assisted notes cannot select independent in the form", async () => {
    const { ids, basis } = await ui({ assistedImport: true });
    ids.get("import-file").files = [{ size: 2, text: async () => "[]" }];
    ids.get("import").onclick();
    await drain();
    // The app resumes on the first unsaved question; inspect the imported first one.
    ids.get("previous").onclick();
    assert.equal(basis[0].disabled, true);
    assert.equal(basis[1].checked, true);
});
