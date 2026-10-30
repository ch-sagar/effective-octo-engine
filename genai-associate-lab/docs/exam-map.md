# Exam objective → where you practise it
Based on the Databricks Certified Generative AI Engineer Associate exam guide dated Mar 2026. ✅ = hands-on in the lab · 📖 = explained in `extensions.md`, not runnable on Free Edition.

## 1. Design Applications
| Objective | Where |
|---|---|
| Prompt that elicits specific format | ✅ NB01 §1.1–1.2 |
| Select model tasks for business requirement | ✅ NB01 §1.4, NB08 §8.5 |
| Select chain components for inputs/outputs | ✅ NB05 (`rag_model.py`) |
| Translate business goals into inputs/outputs | ✅ `rag_model.py` signature, NB05 §5.3 |
| Define & order tools for multi-stage reasoning | ✅ NB06 |
| Agent Bricks (Knowledge Assistant, Supervisor, Info Extraction) | 📖 extensions (Knowledge Assistant unsupported on Free) |

## 2. Data Preparation
| Objective | Where |
|---|---|
| Chunking strategy per structure/constraints | ✅ NB02 §2.3–2.4 |
| Filter extraneous content | ✅ NB02 §2.2 |
| Choose Python package per format | ✅ `cleaning.PARSER_FOR_EXTENSION` |
| Write chunks to Delta in UC | ✅ NB02 §2.4 |
| Identify source documents of needed quality | ✅ NB02 §2.1 |
| Metrics to evaluate retrieval | ✅ NB04 |
| Advanced chunking (header-aware, sentence-window) | ✅ `chunking.py` |
| Role of re-ranking | ✅ NB03 §3.5 |

## 3. Application Development
| Objective | Where |
|---|---|
| LangChain/similar tools | 📖 extensions (LangGraph variant); manual loop in `agent.py` |
| Qualitative response assessment | ✅ NB07 §7.3 |
| Chunking based on retrieval eval | ✅ NB04 |
| Prompt augmentation with context | ✅ NB01 §1.3, `rag_model.py` |
| Adjust response baseline → desired | ✅ NB01, NB07 §7.4 |
| Guardrails | ✅ `guardrails.py`, NB05 §5.2 |
| Select LLM by attributes/metrics | ✅ NB01 §1.4 |
| Embedding model context length | ✅ NB02 "Try it" |
| Choose model from hub via model cards | 📖 Marketplace limited on Free |
| MLflow + Agent Framework | ✅ NB06 |
| Evaluation vs monitoring phases | ✅ NB07 end, NB08 §8.4 |
| Multi-agent with Genie | 📖 extensions |

## 4. Assembling & Deploying
| Objective | Where |
|---|---|
| pyfunc with pre/post-processing | ✅ NB05 |
| Control access from serving endpoints | ✅ NB05 §5.3 `resources`, NB09 app resources |
| Simple chain by requirements | ✅ NB05 |
| Basic RAG elements (flavor, embedding, retriever, deps, example, signature) | ✅ NB05 §5.3 |
| Register to UC | ✅ NB05 §5.4 |
| Create & query Vector Search | ✅ NB03 |
| Serve with Foundation Model APIs | ✅ NB08 |
| Vector Search concepts | ✅ NB03 header table |
| `ai_query()` batch | ✅ NB08 §8.5 |
| Configure VS by size/freshness/latency/cost | ✅ NB03 (TRIGGERED vs CONTINUOUS table) |
| Persistent datastore for memory | 📖 extensions (Lakebase) |
| CI/CD (index update, prompt promotion, component tests) | ✅ NB03 §3.6, NB06 §6.3, `tests/`, `.github/` |
| Managed/external/custom MCP | 📖 extensions |
| Prompt version control | ✅ NB06 §6.3 |
| User-facing interface | ✅ NB09 |

## 5. Governance
| Objective | Where |
|---|---|
| Masking as guardrail | ✅ `guardrails.mask_pii`, NB05 |
| Guardrails vs malicious input | ✅ `looks_like_injection`, NB05 §5.2 |
| Licensing/legal for sources | ✅ NB02 §2.1 |
| Alternatives for problematic text in sources | ✅ NB02 (exclude / mask / mitigate) |

## 6. Evaluation & Monitoring
| Objective | Where |
|---|---|
| Choose LLM size by metrics | ✅ NB01 §1.4 |
| Key metrics to monitor | ✅ NB08 §8.4 |
| MLflow scoring & tracing | ✅ NB06, NB07 |
| Inference logging for RAG | ✅ NB08 §8.4 (inference tables) |
| Control LLM cost | ✅ NB08 §8.4 |
| Inference tables & Agent Monitoring | ✅/📖 NB08 (availability varies on Free) |
| Judges requiring ground truth | ✅ NB07 header table |
| AI Gateway | ✅/📖 NB08 §8.4 |
| Custom scorers | ✅ `scorers.py`, NB07 |
| SME feedback | ✅/📖 NB07 §7.5 |
