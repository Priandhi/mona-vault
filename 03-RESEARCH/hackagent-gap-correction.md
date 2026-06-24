# HACKAGENT-AI-SECURITY — GAP CORRECTION
> 2026-06-25 | Self-corrected from official HackAgent docs
> docs source: https://raw.githubusercontent.com/AISecurityLab/hackagent/main/docs/docs/attacks/

## GAPS TERISI (8 dari 8)

### 1. AdvPrefix — 9-step pipeline (sebelumnya cuma "prefix optimization")
- **Step 1: Meta Prefix Generation** — Generator LLM (uncensored) bikin prefix candidates dari template
- **Step 2: Preprocessing** — Filter & validasi prefix quality
- **Step 3: Cross-Entropy Computation** — Hitung model loss scores
- **Step 4: Completion Generation** — Target model respon ke prefixed prompts
- **Step 5: Evaluation** — Judge models nilai attack success & harmfulness
- **Step 6: Aggregation** — Gabungin hasil, hitung comprehensive metrics
- **Step 7: Selection** — Pilih prefix paling efektif berdasarkan scoring
- **Step 8: Result Analysis** — Analisa attack patterns dan success rates
- **Step 9: Reporting** — Generate detailed attack reports
- Konfig: min_char_length (10), max_token_segments (5), n_candidates_per_goal (5), n_prefixes_per_goal (2), batch_size, goal_batch_size, goal_batch_workers, batch_size_judge

### 2. BoN (Best-of-N) — stochastic black-box (sebelumnya "sampling")
- **NO attacker LLM needed** — cuma target model + judge
- **Mechanism**: Generate N augmented candidates per step pake random text transformations:
  - Word Scrambling: shuffle middle chars of words > 3 chars (probability σ^(1/2) per word)
  - Random Capitalization: toggle case randomly (probability σ^(1/2) per char)
  - ASCII Perturbation: shift printable ASCII chars by ±1 (probability σ^3 per char)
- **σ (sigma)**: Augmentation strength (0-1). Default 0.4. Higher = more aggressive.
- **Flow**: Augment K candidates → send parallel → select best by response length → judge evaluates → early stop if jailbreak → repeat next step with fresh seeds
- **Early termination**: Judge dipanggil INLINE dalam search loop, bukan post-processing
- **Total queries per goal**: n_steps × num_concurrent_k (worst case, less if early stopped)
- **Deterministic seeds**: tiap candidate pake seed dari step+candidate index → reproducible

### 3. PAP (Persuasive Adversarial Prompts) — taxonomy-guided (sebelumnya "social engineering")
- **Base paper**: Zeng et al., 2024 — arXiv:2401.06373
- **40 persuasion techniques** dari social science taxonomy
- **Default top-5**: Evidence-based Persuasion, Expert Endorsement, Misrepresentation, Authority Endorsement, Logical Appeal
- **Mechanism**: Attacker LLM rewrite harmful goal pake persuasion technique → persuasive prompt → target model → judge → early stop kalau jailbreak
- **Early stop**: Kalau 1 technique berhasil, techniques lain di-skip
- **Ironi**: LLM yang lebih powerful (GPT-4) LEBIH RENTAN ke PAP
- **Parameter**: techniques ("top5"/"all"/custom list), max_techniques_per_goal, attacker_temperature (1.0), attacker_max_tokens (1024)

### 4. MML (Multi-Modal Linkage) — image-based jailbreak (sebelumnya "gatau")
- **Base paper**: Wang et al., 2024 — arXiv:2412.00473
- **Core exploit**: Encode harmful prompt ke IMAGE → bypass safety classifier yang cuma cek teks
- **5 encoding modes**:
  - word_replacement (default): replace keywords → render modified text ke image → kasih replacement dictionary di prompt teks
  - mirror: render text → flip horizontal
  - rotate: render text → rotate 180°
  - base64: encode ke Base64 → render encoded string
  - mixed: word_replacement + mirror + rotation
- **2 prompt styles**: game (villain's lair scenario), control (neutral list-filling)
- **Target**: Vision-Language Models (VLM) — GPT-4V, Gemini Vision, dll

### 5. tFC-Attack — text-based flowchart jailbreak (baru tau)
- **Base paper**: FC-Attack, Zhang et al., EMNLP 2025 — arXiv:2502.21059
- **Target**: Text-only LLMs (bukan VLM)
- **Mechanism**: Harmful goal → decompose into steps → optionally truncate last step → serialize as graph description text → send to LLM
- **5 text formats**: DOT, Mermaid, TikZ, PlantUML, ASCII art
- **3 layouts**: vertical, horizontal, tortuous (S-shaped)
- **Key trick**: Last step di-truncate → model "complete" harmful content
- **Sibling attack**: FC-Attack (image version for VLMs)

### 6. FC-Attack — flowchart image jailbreak (baru tau)
- Sama kayak tFC tapi render flowchart sebagai IMAGE (Graphviz) untuk VLM
- Competitive quiz scenario prompt buat jailbreak

### 7. RAG Attack — indirect injection via poisoned documents (sebelumnya cuma "vault poisoning")
- **Risk microcategory**: Indirect Injection
- **HackAgent handle ENTIRE RAG pipeline** — target agent cuma LLM endpoint
- **Pipeline**: Source docs → Poisoner bikin payload → Inject ke document → Chunk + embed → Build FAISS index → Generate benign queries → RAG query → Target agent → Judge
- **3 strategies**:
  - inline_context_override: Blend payload ke surrounding prose, maximum stealth
  - append_hidden_directive: Explicit assistant-facing guidance ("when answering, do X"), strongest signal
  - maximize_retrieval: Q+P anchor — prefix malicious paragraph dengan benign query text biar embedding mirip → menang retrieval competition
- **Poisoner hanya generate payload paragraph** — bukan seluruh dokumen (token efficient)
- **Insertion point**: Dipilih via embedding similarity ke benign query anchor

### 8. Baseline — predefined template attacks (sebelumnya "gatau fungsinya")
- **Purpose**: Quick vulnerability scans, regression testing, establishing baselines
- **Mechanism**: Combine known jailbreak templates with test objectives
- **Template categories**: roleplay, encoding, context_switch
- **Parameters**: template_categories, templates_per_category
- **FAST** — minutes, bukan hours

## ATTACK TYPES FULL MAP (15 attacks di HackAgent)
| # | Attack | Type | Needs Attacker LLM | Target |
|---|--------|------|-------------------|--------|
| 1 | AdvPrefix | Adversarial Prefix | Yes (uncensored) | Text LLM |
| 2 | AutoDAN-Turbo | Lifelong Strategy | Yes (3 roles) | Text LLM |
| 3 | PAIR | Iterative Refinement | Yes (2 LLMs) | Text LLM |
| 4 | TAP | Tree Search | Yes (2 LLMs) | Text LLM |
| 5 | BoN | Random Augmentation | NO | Text LLM |
| 6 | FlipAttack | Character Reversal | NO | Text LLM |
| 7 | CipherChat | Cipher Encoding | NO | Text LLM |
| 8 | PAP | Persuasion | Yes (attacker LLM) | Text LLM |
| 9 | h4rm3l | Chain Decorator | Yes (generator) | Text LLM |
| 10 | Baseline | Templates | NO | Text LLM |
| 11 | MML | Image Encoding | NO | VLM |
| 12 | FC | Flowchart Image | Yes (step gen) | VLM |
| 13 | tFC | Text Flowchart | Yes (step gen) | Text LLM |
| 14 | RAG | Doc Poisoning | Yes (poisoner) | RAG Agent |
| 15 | (agent-specific) | Framework-native | NO | Agent SDK |

## PENGUASAAN BARU
- AdvPrefix: 75% → 90% (tau full 9-step + parameter tuning)
- BoN: 30% → 85% (tau augmentation math + sigma + early stop)
- PAP: 35% → 85% (tau 40 techniques + early stop + irony)
- MML: 5% → 80% (tau 5 encoding modes + 2 prompt styles)
- tFC/FC: 0% → 75% (baru tau, ngerti mechanism)
- RAG: 40% → 85% (tau 3 strategies + full pipeline)
- Baseline: 20% → 70% (tau purpose + categories)

**Overall hackagent-ai-security: 25% → ~80%**
