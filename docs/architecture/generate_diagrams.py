import os
import sys
import xml.etree.ElementTree as ET
import json
import subprocess
import pathlib

font_family = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"

def build_hld():
    xml = []
    xml.append('<mxfile host="Electron" modified="2026-11-06T15:35:00.000Z" version="24.0.0" type="device">')
    xml.append('  <diagram id="reckon-hld" name="Reckon High-Level Design">')
    xml.append('    <mxGraphModel dx="1740" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1740" pageHeight="1000" math="0" shadow="0">')
    xml.append('      <root>')
    xml.append('        <mxCell id="0" />')
    xml.append('        <mxCell id="1" parent="0" />')

    # Top Header & Status Badge
    xml.append(f'''
        <mxCell id="title_block" value="&lt;b style=&quot;font-size:22px;color:#0f172a;&quot;&gt;RECKON &amp;#8212; High-Level System Architecture (HLD)&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:13px;color:#475569;&quot;&gt;Selective RAG Decision Framework &amp;#8226; Multi-Layer Network Isolation &amp;#8226; Local Docker Compose Deployment&lt;/span&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=0;strokeColor=none;fillColor=none;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="35" y="20" width="850" height="50" as="geometry" />
        </mxCell>
        <mxCell id="status_badge" value="&lt;b style=&quot;color:#166534;font-size:12px;&quot;&gt;VERIFIED LOCAL DOCKER ARCHITECTURE&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;color:#334155;font-size:11px;&quot;&gt;Loopback Bound (127.0.0.1) &amp;#8226; Air-Gapped Internal Bridge &amp;#8226; Non-Root Least Privilege&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#86efac;strokeWidth=1.5;fontFamily={font_family};align=center;" vertex="1" parent="1">
          <mxGeometry x="1140" y="20" width="560" height="46" as="geometry" />
        </mxCell>
    ''')

    # Boundary 1: Host Environment (Developer Laptop)
    xml.append(f'''
        <mxCell id="host_boundary" value="&lt;b style=&quot;font-size:13px;color:#475569;&quot;&gt;HOST ENVIRONMENT (Developer Laptop)&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#94a3b8;strokeWidth=1.5;dashed=1;verticalAlign=top;align=center;spacingTop=10;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="35" y="85" width="220" height="870" as="geometry" />
        </mxCell>

        <!-- Block 1: User Web Browser -->
        <mxCell id="user_client" value="&lt;b style=&quot;font-size:14px;color:#0f172a;&quot;&gt;User Web Browser&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:11px;color:#475569;&quot;&gt;Interactive Research UI&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #cbd5e1;margin:8px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#334155;line-height:1.5;&quot;&gt;&amp;#8226; URL: &lt;b&gt;http://127.0.0.1:3000&lt;/b&gt;&lt;br/&gt;&amp;#8226; Query Lab &amp;amp; Ledger (&lt;i&gt;/&lt;/i&gt;)&lt;br/&gt;&amp;#8226; Evaluation Dashboard (&lt;i&gt;/evaluation&lt;/i&gt;)&lt;br/&gt;&amp;#8226; Experiment Runner (&lt;i&gt;/experiments&lt;/i&gt;)&lt;br/&gt;&amp;#8226; Corpus Explorer (&lt;i&gt;/corpus&lt;/i&gt;)&lt;br/&gt;&amp;#8226; Strict Loopback Access Only&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#64748b;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=10;" vertex="1" parent="1">
          <mxGeometry x="50" y="160" width="190" height="195" as="geometry" />
        </mxCell>

        <!-- Block 2: Host Ollama Runtime -->
        <mxCell id="host_ollama" value="&lt;b style=&quot;font-size:14px;color:#b45309;&quot;&gt;Local Ollama Engine&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:11px;color:#78350f;&quot;&gt;Host Process (Bare-Metal)&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fde68a;margin:8px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#451a03;line-height:1.5;&quot;&gt;&amp;#8226; Binds: &lt;b&gt;127.0.0.1:11434&lt;/b&gt;&lt;br/&gt;&amp;#8226; LLM: &lt;b&gt;qwen3:4b-q4_K_M&lt;/b&gt;&lt;br/&gt;&amp;#8226; Embed: &lt;b&gt;all-minilm:22m&lt;/b&gt; (BERT-384)&lt;br/&gt;&amp;#8226; Isolated from containers&lt;br/&gt;&amp;#8226; Reached via internal relay&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#d97706;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=10;" vertex="1" parent="1">
          <mxGeometry x="50" y="630" width="190" height="190" as="geometry" />
        </mxCell>
    ''')

    # Boundary 2: Docker Compose Environment
    xml.append(f'''
        <mxCell id="docker_boundary" value="&lt;b style=&quot;font-size:14px;color:#0369a1;&quot;&gt;DOCKER COMPOSE TOPOLOGY (compose.yaml)&lt;/b&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;font-size:11px;color:#64748b;&quot;&gt;Non-root UIDs &amp;#8226; cap_drop: ALL &amp;#8226; read_only root filesystems &amp;#8226; no-new-privileges&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#0284c7;strokeWidth=2;dashed=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="275" y="85" width="1425" height="870" as="geometry" />
        </mxCell>
    ''')

    # Column A: Perimeter Gateway Container (reckon-gateway-1)
    xml.append(f'''
        <mxCell id="container_gateway" value="&lt;b style=&quot;font-size:13px;color:#0369a1;&quot;&gt;PERIMETER GATEWAY (reckon-gateway-1)&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#64748b;&quot;&gt;Image: reckon-nginx:p6-local &amp;#8226; Bridge: ingress, local&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f0f9ff;strokeColor=#38bdf8;strokeWidth=1.5;verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="295" y="125" width="280" height="810" as="geometry" />
        </mxCell>

        <!-- Block 3: HTTP Ingress Proxy -->
        <mxCell id="gateway_ingress_proxy" value="&lt;b style=&quot;font-size:13px;color:#0c4a6e;&quot;&gt;HTTP Ingress Proxy (:8080)&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:11px;color:#0369a1;&quot;&gt;Host Port: 127.0.0.1:3000&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #bae6fd;margin:8px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#0f172a;line-height:1.45;&quot;&gt;&amp;#8226; &lt;b&gt;Header Scrubbing:&lt;/b&gt; Drops X-Forwarded-*, Authorization, Cookie headers&lt;br/&gt;&amp;#8226; &lt;b&gt;Host Validation:&lt;/b&gt; Enforces 127.0.0.1&lt;br/&gt;&amp;#8226; &lt;b&gt;Payload Guard:&lt;/b&gt; Capped at 1MB&lt;br/&gt;&amp;#8226; &lt;b&gt;Routes / &amp;amp; /api/:&lt;/b&gt; Reverse proxies to internal pod &lt;b&gt;http://backend:8080&lt;/b&gt;&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#7dd3fc;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="310" y="180" width="250" height="195" as="geometry" />
        </mxCell>

        <!-- Block 4: Ollama Whitelist Relay -->
        <mxCell id="gateway_ollama_relay" value="&lt;b style=&quot;font-size:13px;color:#92400e;&quot;&gt;Ollama Whitelist Relay (:11434)&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:11px;color:#b45309;&quot;&gt;Internal-Only Egress Relay&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fde68a;margin:8px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#451a03;line-height:1.45;&quot;&gt;&amp;#8226; Bound to air-gapped &lt;b&gt;local&lt;/b&gt; network&lt;br/&gt;&amp;#8226; &lt;b&gt;Strict Endpoint Whitelist:&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;&amp;#8226; GET /api/tags, GET /api/version&lt;br/&gt;&amp;nbsp;&amp;nbsp;&amp;#8226; POST /api/show&lt;br/&gt;&amp;nbsp;&amp;nbsp;&amp;#8226; POST /api/chat (Generation)&lt;br/&gt;&amp;nbsp;&amp;nbsp;&amp;#8226; POST /api/embed (Embeddings)&lt;br/&gt;&amp;#8226; &lt;b&gt;Other Paths:&lt;/b&gt; Immediate HTTP 404&lt;br/&gt;&amp;#8226; Target: &lt;b&gt;host.docker.internal:11434&lt;/b&gt;&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#f59e0b;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="310" y="610" width="250" height="215" as="geometry" />
        </mxCell>
    ''')

    # Column B: Shared Network Pod (network_mode: service:backend)
    xml.append(f'''
        <mxCell id="pod_boundary" value="&lt;b style=&quot;font-size:13.5px;color:#166534;&quot;&gt;SHARED APPLICATION POD (network_mode: service:backend)&lt;/b&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;font-size:11px;color:#475569;&quot;&gt;Shared 127.0.0.1 Loopback &amp;#8226; Air-Gapped (internal: true)&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=2;dashed=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=8;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="605" y="125" width="745" height="810" as="geometry" />
        </mxCell>

        <!-- Block 5: Internal App Proxy -->
        <mxCell id="container_app_proxy" value="&lt;b style=&quot;font-size:13px;color:#0f172a;&quot;&gt;Internal Dispatcher Proxy (reckon-app-proxy-1)&lt;/b&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;font-size:11px;color:#64748b;&quot;&gt;Ports: 127.0.0.1:8080 &amp;amp; :11434&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #cbd5e1;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#334155;line-height:1.4;&quot;&gt;&amp;#8226; &lt;b&gt;:8080/api/&lt;/b&gt; &amp;rarr; Routes to FastAPI Backend on &lt;b&gt;127.0.0.1:8000&lt;/b&gt;&lt;br/&gt;&amp;#8226; &lt;b&gt;:8080/&lt;/b&gt; &amp;rarr; Routes to Next.js Frontend on &lt;b&gt;127.0.0.1:3000&lt;/b&gt;&lt;br/&gt;&amp;#8226; &lt;b&gt;:11434/&lt;/b&gt; &amp;rarr; Forwards backend Ollama requests to &lt;b&gt;gateway:11434&lt;/b&gt;&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#94a3b8;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="625" y="165" width="705" height="85" as="geometry" />
        </mxCell>

        <!-- Block 6: Next.js Frontend -->
        <mxCell id="container_frontend" value="&lt;b style=&quot;font-size:13px;color:#0e7490;&quot;&gt;Frontend Service (reckon-frontend-1)&lt;/b&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;font-size:11px;color:#64748b;&quot;&gt;Next.js 16.4 / React 19 / Node 24 &amp;#8226; Listens: 127.0.0.1:3000&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #cffafe;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#164e63;line-height:1.4;&quot;&gt;&amp;#8226; &lt;b&gt;Query Lab &amp;amp; Ledger:&lt;/b&gt; Interactive question execution, evidence citation inspector, and latency breakdown&lt;br/&gt;&amp;#8226; &lt;b&gt;Evaluation Dashboard:&lt;/b&gt; Visualizes Risk-Coverage curve, Policy comparisons, and Reliability diagrams&lt;br/&gt;&amp;#8226; &lt;b&gt;Typed API Client:&lt;/b&gt; Strict JSON contract validation, cancellation signals, bounded reads&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ecfeff;strokeColor=#06b6d4;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="625" y="270" width="705" height="95" as="geometry" />
        </mxCell>

        <!-- Block 7: Backend Service Container & Principal Subsystems -->
        <mxCell id="container_backend" value="&lt;b style=&quot;font-size:13.5px;color:#166534;&quot;&gt;Backend Service (reckon-backend-1)&lt;/b&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;font-size:11px;color:#475569;&quot;&gt;FastAPI / Python 3.13 / Uvicorn &amp;#8226; Listens: 127.0.0.1:8000&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#15803d;strokeWidth=1.5;verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="625" y="385" width="705" height="530" as="geometry" />
        </mxCell>

        <!-- Subsystem 7A: API Layer -->
        <mxCell id="subsys_api" value="&lt;b style=&quot;font-size:12px;color:#0f172a;&quot;&gt;FastAPI API Layer &amp;amp; Middleware (app.api)&lt;/b&gt;&lt;br/&gt;&lt;div style=&quot;font-size:10.5px;color:#334155;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; &lt;b&gt;POST /api/v1/query:&lt;/b&gt; Interactive single-query orchestration &amp;amp; citations&lt;br/&gt;&amp;#8226; &lt;b&gt;POST /api/v1/experiments/jobs:&lt;/b&gt; Asynchronous batch benchmark job execution&lt;br/&gt;&amp;#8226; &lt;b&gt;Strict Security:&lt;/b&gt; Local loopback enforcement, CORS origin lock, request size limits&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#cbd5e1;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="640" y="420" width="675" height="80" as="geometry" />
        </mxCell>

        <!-- Subsystem 7B: Retrieval Engine -->
        <mxCell id="subsys_retrieval" value="&lt;b style=&quot;font-size:12px;color:#14532d;&quot;&gt;Retrieval Subsystem (app.retrieval)&lt;/b&gt;&lt;br/&gt;&lt;div style=&quot;font-size:10.5px;color:#14532d;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; &lt;b&gt;BM25 Lexical:&lt;/b&gt; Okapi BM25 index (k1=1.5, b=0.75) with character offsets&lt;br/&gt;&amp;#8226; &lt;b&gt;Dense Cosine:&lt;/b&gt; all-minilm:22m (384-dim BERT) embeddings via Ollama /api/embed&lt;br/&gt;&amp;#8226; &lt;b&gt;Hybrid RRF:&lt;/b&gt; Reciprocal Rank Fusion (k=60) over merged candidate pools &amp;#8226; LRU Cache (Capacity 8)&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#86efac;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="640" y="515" width="675" height="85" as="geometry" />
        </mxCell>

        <!-- Subsystem 7C: Decision & Generation Engine -->
        <mxCell id="subsys_generation" value="&lt;b style=&quot;font-size:12px;color:#78350f;&quot;&gt;Decision &amp;amp; Generation Engine (app.generation)&lt;/b&gt;&lt;br/&gt;&lt;div style=&quot;font-size:10.5px;color:#78350f;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; &lt;b&gt;Threshold Abstention:&lt;/b&gt; Short-circuits prior to generation if max retrieval score &amp;lt; threshold&lt;br/&gt;&amp;#8226; &lt;b&gt;Prompt Abstention:&lt;/b&gt; Structured sufficiency judgment (insufficient, conflicting, or out-of-scope)&lt;br/&gt;&amp;#8226; &lt;b&gt;Exact Citation Verification:&lt;/b&gt; Character-slice containment [start_char, end_char] against chunks&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#fde68a;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="640" y="615" width="675" height="85" as="geometry" />
        </mxCell>

        <!-- Subsystem 7D: Experiment & Evaluation Engine -->
        <mxCell id="subsys_eval" value="&lt;b style=&quot;font-size:12px;color:#0e7490;&quot;&gt;Experiment &amp;amp; Evaluation Engine (app.evaluation &amp;amp; app.db)&lt;/b&gt;&lt;br/&gt;&lt;div style=&quot;font-size:10.5px;color:#164e63;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; &lt;b&gt;Experiment Jobs Queue:&lt;/b&gt; Bounded worker (1 running, 4 queued) with atomic SQLite transactions&lt;br/&gt;&amp;#8226; &lt;b&gt;Selective Risk-Coverage:&lt;/b&gt; Computes Coverage &amp;Phi;(&amp;tau;), Selective Risk R(&amp;tau;), and right-step AURC&lt;br/&gt;&amp;#8226; &lt;b&gt;Confidence Calibration:&lt;/b&gt; Binned reliability diagrams and paired bootstrap intervals&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ecfeff;strokeColor=#a5f3fc;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="640" y="715" width="675" height="85" as="geometry" />
        </mxCell>
    ''')

    # Column C: Storage & Data Persistence Subsystem
    xml.append(f'''
        <mxCell id="storage_boundary" value="&lt;b style=&quot;font-size:13px;color:#78350f;&quot;&gt;PERSISTENT STORAGE &amp;amp; DATA MOUNTS&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#d97706;strokeWidth=1.5;dashed=1;verticalAlign=top;align=center;spacingTop=8;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="1375" y="125" width="305" height="810" as="geometry" />
        </mxCell>

        <!-- Block 8: Named State Volume -->
        <mxCell id="volume_state" value="&lt;b style=&quot;font-size:13px;color:#92400e;&quot;&gt;Docker Named Volume (state:/state)&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:11px;color:#b45309;&quot;&gt;Runtime Persistence&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fde68a;margin:8px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#451a03;line-height:1.45;&quot;&gt;&amp;#8226; &lt;b&gt;/state/experiments.sqlite3:&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;- Table &lt;i&gt;jobs&lt;/i&gt; (payloads, results)&lt;br/&gt;&amp;nbsp;&amp;nbsp;- Table &lt;i&gt;freezes&lt;/i&gt; (immutable baselines)&lt;br/&gt;&amp;#8226; &lt;b&gt;/state/experiments.lock:&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;- OS file-locking mechanism&lt;br/&gt;&amp;#8226; &lt;b&gt;/state/dense/:&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;- Precomputed document vectors&lt;br/&gt;&amp;#8226; Persists across all restarts&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="1390" y="165" width="275" height="220" as="geometry" />
        </mxCell>

        <!-- Block 9: Read-Only Host Mounts -->
        <mxCell id="mounted_corpus" value="&lt;b style=&quot;font-size:13px;color:#78350f;&quot;&gt;Read-Only Host Mounts (:ro)&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:11px;color:#92400e;&quot;&gt;Immutable Test Datasets&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fde68a;margin:8px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#451a03;line-height:1.45;&quot;&gt;&amp;#8226; &lt;b&gt;data/benchmark/documents.jsonl:ro&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;Python stdlib source documentation with character-offset ground truth&lt;br/&gt;&lt;br/&gt;&amp;#8226; &lt;b&gt;data/fixtures/p4_synthetic_v1:ro&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;Synthetic development evaluation split (train &amp;amp; dev questions; no leakage)&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="1390" y="415" width="275" height="210" as="geometry" />
        </mxCell>

        <!-- Block 10: Research Asset Boundary -->
        <mxCell id="research_isolation" value="&lt;b style=&quot;font-size:13px;color:#78350f;&quot;&gt;Research Asset Isolation&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:11px;color:#92400e;&quot;&gt;Unaccepted Asset Boundary&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fde68a;margin:8px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#451a03;line-height:1.45;&quot;&gt;&amp;#8226; &lt;b&gt;B2 Candidate Benchmark:&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;Maintained in &lt;i&gt;research/benchmarks/&lt;/i&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;Explicitly marked &lt;b&gt;UNACCEPTED&lt;/b&gt;&lt;br/&gt;&amp;#8226; &lt;b&gt;Pilot30 Audit Infrastructure:&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;Review tooling only; no human claims&lt;br/&gt;&amp;#8226; &lt;b&gt;Strict Isolation:&lt;/b&gt; Not mounted to runtime&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#d97706;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="1390" y="650" width="275" height="210" as="geometry" />
        </mxCell>
    ''')

    # Non-colliding, cleanly routed connectors
    edge_style = f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;fontFamily={font_family};fontSize=11;labelBackgroundColor=#ffffff;labelBorderColor=#cbd5e1;fontColor=#0f172a;"

    xml.append(f'''
        <!-- 1. Browser to Gateway Ingress -->
        <mxCell id="edge_user_gateway" value="HTTP&lt;br/&gt;127.0.0.1:3000" style="{edge_style};strokeColor=#0284c7;strokeWidth=2;fontColor=#0369a1;" edge="1" parent="1" source="user_client" target="gateway_ingress_proxy">
          <mxGeometry relative="1" as="geometry">
            <mxPoint y="-14" as="offset" />
          </mxGeometry>
        </mxCell>

        <!-- 2. Gateway to App Proxy -->
        <mxCell id="edge_gateway_proxy" value="Proxy Pass (:8080)" style="{edge_style};strokeColor=#0284c7;strokeWidth=2;fontColor=#0369a1;" edge="1" parent="1" source="gateway_ingress_proxy" target="container_app_proxy">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="585" y="277" />
              <mxPoint x="585" y="207" />
            </Array>
            <mxPoint y="-14" as="offset" />
          </mxGeometry>
        </mxCell>

        <!-- 3. App Proxy to Frontend UI -->
        <mxCell id="edge_proxy_frontend" value="Web Routes (/*)" style="{edge_style};strokeColor=#06b6d4;strokeWidth=1.5;fontColor=#0e7490;" edge="1" parent="1" source="container_app_proxy" target="container_frontend">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="55" y="-5" as="offset" />
          </mxGeometry>
        </mxCell>

        <!-- 4. App Proxy to Backend API -->
        <mxCell id="edge_proxy_backend" value="API Routes (/api/*)" style="{edge_style};strokeColor=#16a34a;strokeWidth=1.5;fontColor=#166534;" edge="1" parent="1" source="container_app_proxy" target="subsys_api">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1320" y="235" />
              <mxPoint x="1320" y="460" />
            </Array>
            <mxPoint x="-45" y="-12" as="offset" />
          </mxGeometry>
        </mxCell>

        <!-- 5. Backend to Internal Ollama Egress Relay -->
        <mxCell id="edge_backend_egress" value="LLM &amp; Embed Calls (:11434)" style="{edge_style};strokeColor=#d97706;strokeWidth=1.5;fontColor=#b45309;" edge="1" parent="1" source="subsys_generation" target="gateway_ollama_relay">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="590" y="657" />
              <mxPoint x="590" y="717" />
            </Array>
            <mxPoint y="-14" as="offset" />
          </mxGeometry>
        </mxCell>

        <!-- 6. Gateway Relay to Host Ollama -->
        <mxCell id="edge_relay_ollama" value="Whitelisted Relay Calls" style="{edge_style};strokeColor=#d97706;strokeWidth=2;fontColor=#b45309;" edge="1" parent="1" source="gateway_ollama_relay" target="host_ollama">
          <mxGeometry relative="1" as="geometry">
            <mxPoint y="-14" as="offset" />
          </mxGeometry>
        </mxCell>

        <!-- 7. Backend to Volume Storage -->
        <mxCell id="edge_backend_storage" value="SQLite Persistence" style="{edge_style};strokeColor=#d97706;strokeWidth=1.5;fontColor=#b45309;" edge="1" parent="1" source="subsys_eval" target="volume_state">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1350" y="757" />
              <mxPoint x="1350" y="275" />
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- 8. Backend to Host Mounts -->
        <mxCell id="edge_backend_mounts" value="Read Corpus (:ro)" style="{edge_style};strokeColor=#d97706;strokeWidth=1.5;fontColor=#b45309;" edge="1" parent="1" source="subsys_retrieval" target="mounted_corpus">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1340" y="557" />
              <mxPoint x="1340" y="520" />
            </Array>
            <mxPoint y="-14" as="offset" />
          </mxGeometry>
        </mxCell>
    ''')

    xml.append('      </root>')
    xml.append('    </mxGraphModel>')
    xml.append('  </diagram>')
    xml.append('</mxfile>')
    return '\n'.join(xml)


def build_lld():
    xml = []
    xml.append('<mxfile host="Electron" modified="2026-11-06T15:35:00.000Z" version="24.0.0" type="device">')
    xml.append('  <diagram id="reckon-lld" name="Reckon Low-Level Design Pipeline">')
    xml.append('    <mxGraphModel dx="1840" dy="1140" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1840" pageHeight="1140" math="0" shadow="0">')
    xml.append('      <root>')
    xml.append('        <mxCell id="0" />')
    xml.append('        <mxCell id="1" parent="0" />')

    # Top Header & Status Badge
    xml.append(f'''
        <mxCell id="lld_title" value="&lt;b style=&quot;font-size:22px;color:#0f172a;&quot;&gt;RECKON &amp;#8212; Low-Level Design (LLD): Query Execution &amp;amp; Decision Logic&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:13px;color:#475569;&quot;&gt;Deterministic Query Flow &amp;#8226; Pre-Check Short-Circuiting &amp;#8226; Grounded Citation Verification &amp;#8226; Distinct Batch Experiment Branch&lt;/span&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=0;strokeColor=none;fillColor=none;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="35" y="20" width="1050" height="50" as="geometry" />
        </mxCell>
        <mxCell id="lld_badge" value="&lt;b style=&quot;color:#166534;font-size:12px;&quot;&gt;VERIFIED LOCAL PIPELINE CONTRACTS&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;color:#334155;font-size:11px;&quot;&gt;Pre-Check Compute Savings &amp;#8226; Exact Offset Substring Slicing &amp;#8226; Explicit Failure Codes&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#86efac;strokeWidth=1.5;fontFamily={font_family};align=center;" vertex="1" parent="1">
          <mxGeometry x="1230" y="20" width="575" height="46" as="geometry" />
        </mxCell>
    ''')

    # ZONE 1: MAIN INTERACTIVE QUESTION PROCESSING FLOW (POST /api/v1/query)
    xml.append(f'''
        <mxCell id="zone1_container" value="&lt;b style=&quot;font-size:14px;color:#0369a1;&quot;&gt;MAIN INTERACTIVE QUERY FLOW (POST /api/v1/query &amp;rarr; Query Lab)&lt;/b&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;font-size:11px;color:#64748b;&quot;&gt;Synchronous interactive query lifecycle &amp;#8226; Ephemeral response &amp;#8226; Never persists to SQLite or updates dashboard&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#0284c7;strokeWidth=2;dashed=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="35" y="85" width="1215" height="700" as="geometry" />
        </mxCell>
    ''')

    # Stage 1: Request Ingress & Validation
    xml.append(f'''
        <mxCell id="s1_box" value="&lt;b style=&quot;font-size:13px;color:#0369a1;&quot;&gt;STAGE 1: REQUEST VALIDATION&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#64748b;&quot;&gt;app.api.routes.query&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #bae6fd;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#0f172a;line-height:1.45;&quot;&gt;&lt;b&gt;POST /api/v1/query&lt;/b&gt;&lt;br/&gt;&amp;#8226; Body: &lt;b&gt;QueryRequest&lt;/b&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;- question: str&lt;br/&gt;&amp;nbsp;&amp;nbsp;- retrieval: {{&quot;method&quot;, &quot;top_k&quot;}}&lt;br/&gt;&amp;nbsp;&amp;nbsp;- policy: {{&quot;name&quot;, &quot;threshold&quot;}}&lt;br/&gt;&amp;nbsp;&amp;nbsp;- generation: {{&quot;model&quot;, &quot;temperature&quot;}}&lt;br/&gt;&lt;br/&gt;&lt;b&gt;Pydantic Schema Guard:&lt;/b&gt;&lt;br/&gt;&amp;#8226; extra=&quot;forbid&quot;&lt;br/&gt;&amp;#8226; Blocks gold label leakage&lt;br/&gt;&amp;#8226; Rejects invalid params &amp;rarr; HTTP 422&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#38bdf8;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="55" y="130" width="205" height="230" as="geometry" />
        </mxCell>
    ''')

    # Stage 2: Multi-Strategy Retrieval
    xml.append(f'''
        <mxCell id="s2_box" value="&lt;b style=&quot;font-size:13px;color:#166534;&quot;&gt;STAGE 2: RETRIEVAL SUBSYSTEM&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#166534;&quot;&gt;app.retrieval.runtime &amp; app.retrieval.*&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #86efac;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#14532d;line-height:1.45;&quot;&gt;&lt;b&gt;Retrieval Dispatcher:&lt;/b&gt;&lt;br/&gt;&amp;#8226; &lt;b&gt;BM25Index:&lt;/b&gt; Okapi BM25 (k1=1.5, b=0.75)&lt;br/&gt;&amp;#8226; &lt;b&gt;DenseIndex:&lt;/b&gt; all-minilm:22m (384-dim BERT) cosine&lt;br/&gt;&amp;#8226; &lt;b&gt;HybridIndex:&lt;/b&gt; RRF Fusion (k=60)&lt;br/&gt;&lt;br/&gt;&lt;b&gt;Evidence Packaging:&lt;/b&gt;&lt;br/&gt;&amp;#8226; Slices top_k (default 5) chunks&lt;br/&gt;&amp;#8226; Offsets: [start_char, end_char]&lt;br/&gt;&amp;#8226; Aggregates: &lt;b&gt;max_score&lt;/b&gt;&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#22c55e;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="310" y="130" width="225" height="230" as="geometry" />
        </mxCell>
    ''')

    # Stage 3: Policy Pre-Check & Short-Circuit
    xml.append(f'''
        <mxCell id="s3_box" value="&lt;b style=&quot;font-size:13px;color:#78350f;&quot;&gt;STAGE 3: DECISION POLICY PRE-CHECK&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#92400e;&quot;&gt;app.generation.policies &amp; pipeline.py&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fde68a;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#451a03;line-height:1.45;&quot;&gt;&lt;b&gt;Evaluate Active Policy:&lt;/b&gt;&lt;br/&gt;&amp;#8226; &lt;b&gt;Threshold Policy:&lt;/b&gt; Evaluates max_score vs threshold&lt;br/&gt;&amp;#8226; &lt;b&gt;Prompt Abstention:&lt;/b&gt; Structured sufficiency judgment&lt;br/&gt;&amp;#8226; &lt;b&gt;Always Answer:&lt;/b&gt; Baseline policy&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="675" y="130" width="250" height="120" as="geometry" />
        </mxCell>

        <!-- Decision Diamond: max_score >= threshold? -->
        <mxCell id="s3_diamond" value="Score &amp;ge; Threshold?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#d97706;strokeWidth=1.5;fontFamily={font_family};fontSize=12;fontStyle=1;fontColor:#78350f;" vertex="1" parent="1">
          <mxGeometry x="705" y="275" width="175" height="65" as="geometry" />
        </mxCell>

        <!-- Outcome: Short-Circuit Abstention -->
        <mxCell id="s3_short_circuit" value="&lt;b style=&quot;font-size:13px;color:#b91c1c;&quot;&gt;SHORT-CIRCUIT ABSTAIN&lt;/b&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fecaca;margin:5px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#7f1d1d;line-height:1.4;&quot;&gt;&amp;#8226; &lt;b&gt;Decision:&lt;/b&gt; ABSTAIN&lt;br/&gt;&amp;#8226; &lt;b&gt;ReasonCode:&lt;/b&gt; INSUFFICIENT_EVIDENCE&lt;br/&gt;&amp;#8226; &lt;b&gt;Answer:&lt;/b&gt; null &amp;#8226; &lt;b&gt;Citations:&lt;/b&gt; []&lt;br/&gt;&amp;#8226; &lt;b&gt;Compute Saved:&lt;/b&gt; 100% (No LLM Call)&lt;br/&gt;&amp;#8226; Returns HTTP 200 QueryResponse&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fef2f2;strokeColor=#ef4444;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="945" y="245" width="280" height="125" as="geometry" />
        </mxCell>
    ''')

    # Stage 4: Answer Generation
    xml.append(f'''
        <mxCell id="s4_box" value="&lt;b style=&quot;font-size:13px;color:#0e7490;&quot;&gt;STAGE 4: LLM ANSWER GENERATION&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#0e7490;&quot;&gt;app.generation.generator &amp; Ollama Relay&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #a5f3fc;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#164e63;line-height:1.45;&quot;&gt;&amp;#8226; Invokes Ollama &lt;b&gt;POST /api/chat&lt;/b&gt; via internal relay (:11434)&lt;br/&gt;&amp;#8226; Model receives retrieved chunks in &lt;b&gt;EvidenceContext&lt;/b&gt;&lt;br/&gt;&amp;#8226; Generates grounded response with structured citations:&lt;br/&gt;&amp;nbsp;&amp;nbsp;&lt;b&gt;ClaimCitation:&lt;/b&gt; [evidence_id, start_char, end_char, quote]&lt;br/&gt;&amp;#8226; Emits latency &amp;amp; token usage metrics&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#06b6d4;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="55" y="440" width="460" height="150" as="geometry" />
        </mxCell>
    ''')

    # Stage 5: Citation Verification Guard & Outcomes
    xml.append(f'''
        <mxCell id="s5_box" value="&lt;b style=&quot;font-size:13px;color:#166534;&quot;&gt;STAGE 5: EXACT CITATION VERIFICATION GUARD&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#166534;&quot;&gt;app.generation.contracts::validate_citations&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #86efac;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#14532d;line-height:1.45;&quot;&gt;&lt;b&gt;Strict 3-Way Citation Verification Logic:&lt;/b&gt;&lt;br/&gt;1. &lt;b&gt;Chunk ID Integrity:&lt;/b&gt; citation.evidence_id exists in retrieved chunk set&lt;br/&gt;2. &lt;b&gt;Offset Bounds Check:&lt;/b&gt; 0 &amp;le; (end_char - chunk.start) &amp;le; len(chunk.text)&lt;br/&gt;3. &lt;b&gt;Byte-Exact Slice Equality:&lt;/b&gt; chunk.text[start:end] == citation.quote&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#22c55e;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=8;" vertex="1" parent="1">
          <mxGeometry x="565" y="440" width="450" height="150" as="geometry" />
        </mxCell>

        <!-- Citation Validation Diamond -->
        <mxCell id="s5_diamond" value="Citations Valid?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=1.5;fontFamily={font_family};fontSize=12;fontStyle=1;fontColor:#166534;" vertex="1" parent="1">
          <mxGeometry x="705" y="630" width="170" height="65" as="geometry" />
        </mxCell>

        <!-- Outcome A: Verification Failure (HTTP 502) -->
        <mxCell id="s5_failure" value="&lt;b style=&quot;font-size:13px;color:#b91c1c;&quot;&gt;CITATION FAILURE (HTTP 502)&lt;/b&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fecaca;margin:5px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#7f1d1d;line-height:1.4;&quot;&gt;&amp;#8226; Raises ValueError(&quot;quote mismatch&quot;)&lt;br/&gt;&amp;#8226; execution_status = FAILED (decision = null)&lt;br/&gt;&amp;#8226; Returns &lt;b&gt;502 runtime_execution_failure&lt;/b&gt;&lt;br/&gt;&amp;#8226; Blocks hallucinated citations from UI&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fef2f2;strokeColor=#ef4444;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="360" y="620" width="290" height="130" as="geometry" />
        </mxCell>

        <!-- Outcome B: Verified Grounded Answer (HTTP 200) -->
        <mxCell id="s5_success" value="&lt;b style=&quot;font-size:13px;color:#166534;&quot;&gt;VERIFIED ANSWER (HTTP 200)&lt;/b&gt;&lt;hr style=&quot;border:0;border-top:1px solid #86efac;margin:5px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#14532d;line-height:1.4;&quot;&gt;&amp;#8226; &lt;b&gt;Decision:&lt;/b&gt; ANSWER&lt;br/&gt;&amp;#8226; &lt;b&gt;Output:&lt;/b&gt; Grounded answer + verified citations&lt;br/&gt;&amp;#8226; &lt;b&gt;Ledger:&lt;/b&gt; Emits complete retrieval provenance&lt;br/&gt;&amp;#8226; Returns &lt;b&gt;200 QueryResponse&lt;/b&gt; to Query Lab&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=1.5;fontFamily={font_family};verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="935" y="620" width="290" height="130" as="geometry" />
        </mxCell>
    ''')

    # ZONE 2: DISTINCT BRANCH FOR BATCH EXPERIMENTS & RESEARCH EVALUATION
    xml.append(f'''
        <mxCell id="zone2_container" value="&lt;b style=&quot;font-size:13.5px;color:#78350f;&quot;&gt;DISTINCT BRANCH: BATCH EXPERIMENT &amp;amp; EVALUATION PIPELINE&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#92400e;&quot;&gt;Triggered via /experiments UI or benchmark runner &amp;#8212; Decoupled from interactive query loop&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#d97706;strokeWidth=2;dashed=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="1275" y="85" width="530" height="700" as="geometry" />
        </mxCell>

        <!-- E1: Experiment Jobs Queue -->
        <mxCell id="e1_queue" value="&lt;b style=&quot;font-size:13px;color:#78350f;&quot;&gt;1. Bounded Experiment Jobs Runner&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#92400e;&quot;&gt;app.evaluation.experiment_jobs &amp; POST /api/v1/experiments/jobs&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fde68a;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#451a03;line-height:1.45;&quot;&gt;&amp;#8226; Ingests &lt;b&gt;ExperimentRequest&lt;/b&gt; for synthetic cohort (p4_synthetic_v1)&lt;br/&gt;&amp;#8226; &lt;b&gt;Capacity Limit:&lt;/b&gt; Max 5 jobs (1 running, 4 queued in FIFO)&lt;br/&gt;&amp;#8226; Returns &lt;b&gt;HTTP 429 QueueFull&lt;/b&gt; if saturated&lt;br/&gt;&amp;#8226; Dispatches cohort questions through retrieval &amp;amp; policy pipeline&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="1295" y="145" width="490" height="150" as="geometry" />
        </mxCell>

        <!-- E2: SQLite Persistence -->
        <mxCell id="e2_sqlite" value="&lt;b style=&quot;font-size:13px;color:#78350f;&quot;&gt;2. SQLite Durable Persistence&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#92400e;&quot;&gt;app.db.experiments::ExperimentStore &amp; /state/experiments.sqlite3&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #fde68a;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#451a03;line-height:1.45;&quot;&gt;&amp;#8226; &lt;b&gt;Table jobs:&lt;/b&gt; Persists job parameters, questions, decisions, and scores&lt;br/&gt;&amp;#8226; &lt;b&gt;Table freezes:&lt;/b&gt; Saves immutable benchmark baselines (SHA256 locked)&lt;br/&gt;&amp;#8226; &lt;b&gt;Concurrency Lock:&lt;/b&gt; OS file locking prevents database corruption&lt;br/&gt;&amp;#8226; Fully persists across Docker container restarts&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="1295" y="335" width="490" height="150" as="geometry" />
        </mxCell>

        <!-- E3: Research Evaluation Engine -->
        <mxCell id="e3_metrics" value="&lt;b style=&quot;font-size:13px;color:#0e7490;&quot;&gt;3. Research Evaluation &amp;amp; Selective Classification&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:10.5px;color:#0e7490;&quot;&gt;app.evaluation.risk_coverage &amp; POST /api/v1/experiments/{{id}}/analysis&lt;/span&gt;&lt;hr style=&quot;border:0;border-top:1px solid #a5f3fc;margin:6px 0;&quot;/&gt;&lt;div style=&quot;text-align:left;font-size:11px;color:#164e63;line-height:1.45;&quot;&gt;&amp;#8226; &lt;b&gt;Empirical Coverage &amp;Phi;(&amp;tau;):&lt;/b&gt; Answered questions / Total questions (A/N)&lt;br/&gt;&amp;#8226; &lt;b&gt;Selective Risk R(&amp;tau;):&lt;/b&gt; Lexical-proxy risk on answered cohort&lt;br/&gt;&amp;#8226; &lt;b&gt;Right-Step AURC:&lt;/b&gt; Exact right-step integration across saved operating points&lt;br/&gt;&amp;#8226; &lt;b&gt;Uncertainty:&lt;/b&gt; Paired bootstrap confidence intervals (2,000 resamples)&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#06b6d4;strokeWidth=1.2;fontFamily={font_family};verticalAlign=top;spacingTop=6;" vertex="1" parent="1">
          <mxGeometry x="1295" y="525" width="490" height="150" as="geometry" />
        </mxCell>
    ''')

    # BOTTOM ZONE: 5 RESEARCH VISUALIZATION CHARTS
    xml.append(f'''
        <mxCell id="zone3_container" value="&lt;b style=&quot;font-size:13.5px;color:#166534;&quot;&gt;RESEARCH ANALYSIS &amp;amp; VISUALIZATION DASHBOARD (frontend/components/evaluation-dashboard.tsx)&lt;/b&gt;&amp;nbsp;&amp;nbsp;&lt;span style=&quot;font-size:11px;color:#475569;&quot;&gt;Visualizes batch experiment results across 5 verified chart components&lt;/span&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=2;dashed=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=8;fontFamily={font_family};" vertex="1" parent="1">
          <mxGeometry x="35" y="805" width="1770" height="270" as="geometry" />
        </mxCell>

        <!-- Chart 1: Risk-Coverage -->
        <mxCell id="chart_rc" value="&lt;b style=&quot;font-size:12px;color:#0f172a;&quot;&gt;1. Risk&amp;#8211;Coverage Curve&lt;/b&gt;&lt;hr style=&quot;border:0;border-top:1px solid #cbd5e1;margin:4px 0;&quot;/&gt;&lt;div style=&quot;font-size:10.5px;color:#334155;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; Coverage &amp;Phi; on X-axis [0, 1]&lt;br/&gt;&amp;#8226; Selective Risk R on Y-axis [0, 1]&lt;br/&gt;&amp;#8226; Full or partial right-step AURC&lt;br/&gt;&amp;#8226; Plots saved operating points&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#94a3b8;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="55" y="845" width="320" height="210" as="geometry" />
        </mxCell>

        <!-- Chart 2: Policy Comparison -->
        <mxCell id="chart_policy" value="&lt;b style=&quot;font-size:12px;color:#0f172a;&quot;&gt;2. Policy Performance&lt;/b&gt;&lt;hr style=&quot;border:0;border-top:1px solid #cbd5e1;margin:4px 0;&quot;/&gt;&lt;div style=&quot;font-size:10.5px;color:#334155;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; Compares 3 policies side-by-side&lt;br/&gt;&amp;#8226; Always Answer vs Threshold vs Prompt&lt;br/&gt;&amp;#8226; Metrics: Coverage A/N, Risk, Failure Rate&lt;br/&gt;&amp;#8226; Bootstrap confidence intervals&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#94a3b8;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="405" y="845" width="320" height="210" as="geometry" />
        </mxCell>

        <!-- Chart 3: Confidence Calibration -->
        <mxCell id="chart_calib" value="&lt;b style=&quot;font-size:12px;color:#0f172a;&quot;&gt;3. Confidence Calibration&lt;/b&gt;&lt;hr style=&quot;border:0;border-top:1px solid #cbd5e1;margin:4px 0;&quot;/&gt;&lt;div style=&quot;font-size:10.5px;color:#334155;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; Reliability diagram across 10 bins&lt;br/&gt;&amp;#8226; Model confidence vs observed accuracy&lt;br/&gt;&amp;#8226; Diagonal perfect calibration line&lt;br/&gt;&amp;#8226; Uncalibrated scores are not probabilities&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#94a3b8;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="755" y="845" width="320" height="210" as="geometry" />
        </mxCell>

        <!-- Chart 4: Retrieval Performance -->
        <mxCell id="chart_retrieval" value="&lt;b style=&quot;font-size:12px;color:#0f172a;&quot;&gt;4. Retrieval Performance&lt;/b&gt;&lt;hr style=&quot;border:0;border-top:1px solid #cbd5e1;margin:4px 0;&quot;/&gt;&lt;div style=&quot;font-size:10.5px;color:#334155;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; Gold-evidence retrieval recall&lt;br/&gt;&amp;#8226; Active experiment: BM25 / Dense / Hybrid&lt;br/&gt;&amp;#8226; Measured against ground-truth spans&lt;br/&gt;&amp;#8226; No uncomputed MRR or NDCG claimed&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#94a3b8;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="1105" y="845" width="320" height="210" as="geometry" />
        </mxCell>

        <!-- Chart 5: Outcome Breakdown -->
        <mxCell id="chart_outcomes" value="&lt;b style=&quot;font-size:12px;color:#0f172a;&quot;&gt;5. Outcome Breakdown&lt;/b&gt;&lt;hr style=&quot;border:0;border-top:1px solid #cbd5e1;margin:4px 0;&quot;/&gt;&lt;div style=&quot;font-size:10.5px;color:#334155;text-align:left;line-height:1.35;&quot;&gt;&amp;#8226; Stacked distribution per policy &amp;amp; cohort&lt;br/&gt;&amp;#8226; Outcomes: Answer, Abstain, Clarify, Failure&lt;br/&gt;&amp;#8226; Filtered observation counts in ledger&lt;br/&gt;&amp;#8226; Detailed execution error categorization&lt;/div&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#94a3b8;strokeWidth=1;fontFamily={font_family};verticalAlign=top;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="1455" y="845" width="330" height="210" as="geometry" />
        </mxCell>
    ''')

    # Connectors for LLD
    edge_style = f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;fontFamily={font_family};fontSize=11;labelBackgroundColor=#ffffff;labelBorderColor=#cbd5e1;fontColor=#0f172a;"

    xml.append(f'''
        <!-- S1 to S2 (Straight horizontal) -->
        <mxCell id="e_s1_s2" value="Validated Query" style="{edge_style};strokeColor=#0284c7;strokeWidth=2;fontColor=#0369a1;" edge="1" parent="1" source="s1_box" target="s2_box">
          <mxGeometry relative="1" as="geometry">
            <mxPoint y="-14" as="offset" />
          </mxGeometry>
        </mxCell>

        <!-- S2 to S3 (Clean horizontal path with wide gap) -->
        <mxCell id="e_s2_s3" value="EvidenceContext&lt;br/&gt;&amp;amp; Scores" style="{edge_style};strokeColor=#16a34a;strokeWidth=2;fontColor=#166534;" edge="1" parent="1" source="s2_box" target="s3_box">
          <mxGeometry relative="1" as="geometry">
            <mxPoint y="-14" as="offset" />
          </mxGeometry>
        </mxCell>

        <!-- S3 to Diamond (Straight down) -->
        <mxCell id="e_s3_diamond" value="" style="{edge_style};strokeColor=#d97706;strokeWidth=1.5;" edge="1" parent="1" source="s3_box" target="s3_diamond">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Diamond NO to Short-Circuit (Straight right) -->
        <mxCell id="e_diamond_no" value="NO (Score &amp;lt; Threshold)" style="{edge_style};strokeColor=#dc2626;strokeWidth=2;fontColor=#b91c1c;" edge="1" parent="1" source="s3_diamond" target="s3_short_circuit">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Diamond YES to Generator (Stage 4) (Routes through clean vertical gap) -->
        <mxCell id="e_diamond_yes" value="YES (Score &amp;ge; Threshold)" style="{edge_style};strokeColor=#16a34a;strokeWidth=2;fontColor=#166534;" edge="1" parent="1" source="s3_diamond" target="s4_box">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="792" y="395" />
              <mxPoint x="260" y="395" />
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- S4 Generator to S5 Citation Guard (Straight horizontal) -->
        <mxCell id="e_s4_s5" value="Answer &amp;amp; Citations" style="{edge_style};strokeColor=#06b6d4;strokeWidth=2;fontColor=#0e7490;" edge="1" parent="1" source="s4_box" target="s5_box">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- S5 to S5 Diamond (Straight down) -->
        <mxCell id="e_s5_diamond" value="" style="{edge_style};strokeColor=#16a34a;strokeWidth=1.5;" edge="1" parent="1" source="s5_box" target="s5_diamond">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- S5 Diamond NO to Citation Failure (Straight left) -->
        <mxCell id="e_s5_no" value="NO (Invalid / Mismatch)" style="{edge_style};strokeColor=#dc2626;strokeWidth=2;fontColor=#b91c1c;" edge="1" parent="1" source="s5_diamond" target="s5_failure">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- S5 Diamond YES to Verified Success (Straight right) -->
        <mxCell id="e_s5_yes" value="YES (Verified Grounding)" style="{edge_style};strokeColor=#16a34a;strokeWidth=2;fontColor=#166534;" edge="1" parent="1" source="s5_diamond" target="s5_success">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Distinct Branch Connectors (Clean vertical chain) -->
        <!-- E1 to E2 -->
        <mxCell id="e_e1_e2" value="Atomic Commit" style="{edge_style};strokeColor=#d97706;strokeWidth=2;fontColor=#b45309;" edge="1" parent="1" source="e1_queue" target="e2_sqlite">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- E2 to E3 -->
        <mxCell id="e_e2_e3" value="Job Observations" style="{edge_style};strokeColor=#06b6d4;strokeWidth=2;fontColor=#0e7490;" edge="1" parent="1" source="e2_sqlite" target="e3_metrics">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- E3 to Dashboard Zone 3 -->
        <mxCell id="e_e3_dash" value="Generates Visualizations" style="{edge_style};strokeColor=#16a34a;strokeWidth=2;fontColor=#166534;" edge="1" parent="1" source="e3_metrics" target="zone3_container">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1540" y="745" />
              <mxPoint x="1100" y="745" />
              <mxPoint x="1100" y="805" />
            </Array>
          </mxGeometry>
        </mxCell>
    ''')

    xml.append('      </root>')
    xml.append('    </mxGraphModel>')
    xml.append('  </diagram>')
    xml.append('</mxfile>')
    return '\n'.join(xml)


def main():
    os.makedirs("docs/architecture", exist_ok=True)
    os.makedirs("tmp", exist_ok=True)

    print("Building refined HLD diagram XML...")
    hld_xml = build_hld()
    with open("docs/architecture/reckon-hld.drawio", "w", encoding="utf-8") as f:
        f.write(hld_xml)
    ET.fromstring(hld_xml)
    print("HLD drawio XML generated and successfully validated with ElementTree.")

    print("Building refined LLD diagram XML...")
    lld_xml = build_lld()
    with open("docs/architecture/reckon-lld.drawio", "w", encoding="utf-8") as f:
        f.write(lld_xml)
    ET.fromstring(lld_xml)
    print("LLD drawio XML generated and successfully validated with ElementTree.")

    render_script = """
import json
import subprocess
import os
import pathlib

with open('docs/architecture/reckon-hld.drawio', 'r', encoding='utf-8') as f:
    hld_xml = f.read()

with open('docs/architecture/reckon-lld.drawio', 'r', encoding='utf-8') as f:
    lld_xml = f.read()

viewer_path = os.path.abspath('tmp/viewer-static.min.js').replace('\\\\', '/')

def render(xml_content, output_png, width, height):
    xml_json = json.dumps(xml_content)
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Draw.io Render</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #ffffff;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            overflow: hidden;
        }}
        #container {{
            width: {width}px;
            height: {height}px;
            box-sizing: border-box;
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script src="file:///{viewer_path}"></script>
    <script>
        window.addEventListener('load', function() {{
            var xmlStr = {xml_json};
            var parser = new DOMParser();
            var doc = parser.parseFromString(xmlStr, 'text/xml');
            var container = document.getElementById('container');
            var config = {{
                highlight: '#0284c7',
                nav: false,
                toolbar: null,
                edit: null,
                resize: false,
                checkVisibleState: false,
                autoFit: true
            }};
            try {{
                new GraphViewer(container, doc.documentElement, config);
                document.body.setAttribute('data-rendered', 'true');
            }} catch(e) {{
                console.error("GraphViewer render error:", e);
            }}
        }});
    </script>
</body>
</html>'''
    
    html_file = os.path.join('tmp', os.path.basename(output_png).replace('.png', '.html'))
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    html_uri = pathlib.Path(html_file).resolve().as_uri()
    png_abs = os.path.abspath(output_png)
    edge_path = r'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
    cmd = [
        edge_path,
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        '--virtual-time-budget=8000',
        f'--window-size={width + 50},{height + 50}',
        f'--screenshot={png_abs}',
        html_uri
    ]
    subprocess.run(cmd, check=True)
    size = os.path.getsize(png_abs)
    print(f"Rendered {output_png}: {size} bytes")

render(hld_xml, 'docs/architecture/reckon-hld.png', 1740, 1000)
render(lld_xml, 'docs/architecture/reckon-lld.png', 1840, 1140)
"""
    with open("tmp/render.py", "w", encoding="utf-8") as f:
        f.write(render_script)

    print("Executing headless Edge renderer...")
    subprocess.run([sys.executable, "tmp/render.py"], check=True)
    print("Refined diagram generation and PNG rendering complete!")

if __name__ == "__main__":
    main()
