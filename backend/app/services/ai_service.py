from typing import Dict, Any, List, Optional
import os
from google import genai
from google.genai import types
from backend.app.core.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def is_available(self) -> bool:
        return self.client is not None

    async def extract_standard(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Phase 1: Implicit Standard Extraction
        Reverse-engineers the behavioral rules a document demonstrates.
        """
        if not await self.is_available():
            return {"error": "AI Service not configured"}

        prompt = f"""
        You are a document standards analyst. Your job is to REVERSE-ENGINEER the implicit standard 
        that this document follows. The document does NOT declare its rules explicitly — your task 
        is to infer and extract them from the document's actual structure, language, tone, and patterns.

        Analyze the document and extract:

        1. **Document Type**: What kind of document is this? (policy, manual, specification, training, legal, other)
        2. **Authority Model**: How does the document express authority?
           - "governance" = hierarchical policy (Policy → Direction → Framework → Annexes)
           - "safety_first" = safety-critical with WARNING/CAUTION/NOTE blocks
           - "procedural" = step-by-step instructions (Installation → Maintenance → Disassembly)
           - "regulatory" = references external regulations (ASME, ANSI, IEC, ISO)
        3. **Authority Chain**: Extract WHO owns, sponsors, approves, and reviews this document.
           List each entity with their role (owner, sponsor, approver, reviewer) and their level
           in the organizational hierarchy. This is CRITICAL for policy documents.
        4. **Hierarchy Map**: Map the document's internal hierarchy:
           - What levels exist? (e.g. "Policy → Direction → Framework → Annex")
           - Which sections depend on which? (e.g. "Vol 2 depends on Vol 1 Ch1 definitions")
        5. **Obligation Semantics**: For EVERY modal verb found (MUST, SHALL, SHOULD, MAY, COULD, 
           SHALL NOT, MUST NOT), count occurrences and assign enforcement level:
           - MUST / SHALL / SHALL NOT / MUST NOT → "mandatory" (hard requirement, failure = non-compliance)
           - SHOULD / SHOULD NOT → "recommended" (expected, deviation requires justification)
           - MAY / COULD → "optional" (permitted but not required)
           These are NOT style choices — they are ENFORCEABLE obligation levels.
        6. **Language Rules**:
           - Controlled vocabulary: Map each key term to its semantic meaning
           - Tone: formal, instructional, cautionary, conversational
           - Modal verbs used and their enforcement level
        7. **Structure Rules**:
           - Mandatory sections the document demonstrates (infer from what IS present)
           - Whether section ordering is enforced
           - Hierarchy pattern (e.g. "Volume → Chapter → Section → Annex")
        8. **Metadata & Governance**:
           - Versioning discipline (version numbers, dates, document codes)
           - Approval/review blocks
           - Traceability requirements (part numbers, figure references, form numbers)
        9. **Compliance Model**: How would compliance be checked?
           - "audit_based" = Evidence, Non-Conformity, Observations, Good Practice
           - "checklist" = pass/fail against specific items  
           - "regulatory_reference" = compliance with external standards
           - "none" = no formal compliance model detected
        10. **Domain Markers**: Specific domain references found (e.g. ASME, ANSI, IEC, MoD, JSP, NATO)

        IMPORTANT: You ARE inferring implicit rules. Extract what the document DEMONSTRATES, not just what it declares.
        Treat modal verbs as ENFORCEABLE obligations, not as stylistic choices.

        Document Filename: {filename}
        Document Content:
        {text[:200000]}
        """

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=types.Schema(
                        type="OBJECT",
                        properties={
                            "standard_id": {"type": "STRING"},
                            "version": {"type": "STRING"},
                            "status": {"type": "STRING", "enum": ["active", "deprecated", "draft"]},
                            "document_type": {"type": "STRING", "enum": ["policy", "manual", "specification", "training", "legal", "other"]},
                            "authority_model": {"type": "STRING", "enum": ["governance", "safety_first", "procedural", "regulatory"]},
                            "compliance_model": {"type": "STRING", "enum": ["audit_based", "checklist", "regulatory_reference", "none"]},
                            "domain_markers": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "authority_chain": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "level": {"type": "STRING"},
                                        "entity": {"type": "STRING"},
                                        "authority_type": {"type": "STRING", "enum": ["owner", "sponsor", "approver", "reviewer"]}
                                    }
                                }
                            },
                            "hierarchy_map": {
                                "type": "OBJECT",
                                "properties": {
                                    "levels": {"type": "ARRAY", "items": {"type": "STRING"}},
                                    "dependencies": {"type": "ARRAY", "items": {"type": "STRING"}}
                                }
                            },
                            "obligation_semantics": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "term": {"type": "STRING"},
                                        "enforcement_level": {"type": "STRING", "enum": ["mandatory", "recommended", "optional", "forbidden"]},
                                        "count": {"type": "NUMBER"}
                                    }
                                }
                            },
                            "scope": {
                                "type": "OBJECT",
                                "properties": {
                                    "level": {"type": "STRING", "enum": ["file", "folder", "organization"]},
                                    "applies_to": {"type": "STRING"}
                                }
                            },
                            "rules": {
                                "type": "OBJECT",
                                "properties": {
                                    "structure": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "mandatory_sections": {"type": "ARRAY", "items": {"type": "STRING"}},
                                            "section_order_enforced": {"type": "BOOLEAN"},
                                            "hierarchy_pattern": {"type": "STRING"}
                                        }
                                    },
                                    "formatting": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "heading_style": {"type": "STRING", "enum": ["numbered", "roman", "plain"]},
                                            "font_rules": {
                                                "type": "OBJECT",
                                                "properties": {
                                                    "body": {"type": "STRING"},
                                                    "heading": {"type": "STRING"}
                                                }
                                            }
                                        }
                                    },
                                    "language": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "controlled_vocabulary": {"type": "BOOLEAN"},
                                            "controlled_vocabulary_map": {
                                                "type": "OBJECT",
                                                "properties": {
                                                    "must": {"type": "STRING"},
                                                    "should": {"type": "STRING"},
                                                    "may": {"type": "STRING"},
                                                    "shall": {"type": "STRING"},
                                                    "WARNING": {"type": "STRING"},
                                                    "CAUTION": {"type": "STRING"},
                                                    "NOTE": {"type": "STRING"}
                                                }
                                            },
                                            "tone": {"type": "STRING", "enum": ["formal", "instructional", "cautionary", "conversational"]},
                                            "modal_verbs": {"type": "ARRAY", "items": {"type": "STRING"}}
                                        }
                                    },
                                    "metadata": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "versioning_required": {"type": "BOOLEAN"},
                                            "approval_block_required": {"type": "BOOLEAN"},
                                            "traceability": {
                                                "type": "OBJECT",
                                                "properties": {
                                                    "part_numbers": {"type": "BOOLEAN"},
                                                    "figure_references": {"type": "BOOLEAN"},
                                                    "form_numbers": {"type": "BOOLEAN"},
                                                    "annex_references": {"type": "BOOLEAN"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        required=["standard_id", "version", "document_type", "authority_model", "scope", "rules", "authority_chain", "hierarchy_map", "obligation_semantics"]
                    )
                )
            )
            if hasattr(response, 'parsed'):
                return response.parsed
            return response
        except Exception as e:
            return {"error": f"AI extraction failed: {str(e)}"}

    async def evaluate_compliance(self, doc_text: str, standard_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: Domain-Aware Selective Compliance Evaluation
        LLM evaluates compliance with awareness of domain compatibility.
        Now returns a multi-dimension compliance SCORECARD and obligation-level enforcement.
        """
        if not await self.is_available():
            return {"error": "AI Service not configured"}

        prompt = f"""
        You are a policy-aware compliance evaluation engine.
        You evaluate documents against an implicit standard with understanding of authority,
        hierarchy, and obligation semantics — not just formatting and style.

        OBLIGATION-AWARE ENFORCEMENT:
        1. MUST / SHALL / SHALL NOT / MUST NOT violations are HARD FAILURES.
           Any single MUST-level violation means the document is non-compliant.
        2. SHOULD / SHOULD NOT violations are SOFT FAILURES.
           Flag them but they alone do not cause non-compliance.
        3. MAY / COULD are informational only.

        MULTI-DIMENSION SCORING:
        Score each dimension independently on a 0-100 scale:
        - authority_compliance: Does the document have required ownership, approval blocks, sponsor references?
        - obligation_compliance: Are MUST/SHOULD rules correctly used and enforceable? Are obligations preserved?
        - structural_compliance: Does section hierarchy match? Are mandatory sections present in correct order?
        - metadata_compliance: Versioning, document codes, traceability, approval dates present?
        - terminology_compliance: Controlled vocabulary adhered to? Domain terminology correct?

        Compute overall = weighted average:
          (authority * 0.25) + (obligation * 0.30) + (structural * 0.20) + (metadata * 0.15) + (terminology * 0.10)

        DOMAIN COMPATIBILITY:
        1. Determine the DOMAIN of the target document.
        2. Compare against the standard's domain.
        3. If domains are DIFFERENT, only enforce UNIVERSAL rules.
        4. Output compatibility_score (0-100).
        5. If compatibility < 50, include compatibility_warning.
        6. List SKIPPED rules with reasons.

        For each violation, classify its obligation_level (mandatory/recommended/optional).

        Standard Definition (JSON):
        {str(standard_json)}

        Document Content:
        {doc_text[:200000]}
        """

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=types.Schema(
                        type="OBJECT",
                        properties={
                            "compliance_score": {"type": "NUMBER"},
                            "compliant": {"type": "BOOLEAN"},
                            "compatibility_score": {"type": "NUMBER"},
                            "compatibility_warning": {"type": "STRING"},
                            "scorecard": {
                                "type": "OBJECT",
                                "properties": {
                                    "authority_compliance": {"type": "NUMBER"},
                                    "obligation_compliance": {"type": "NUMBER"},
                                    "structural_compliance": {"type": "NUMBER"},
                                    "metadata_compliance": {"type": "NUMBER"},
                                    "terminology_compliance": {"type": "NUMBER"},
                                    "overall": {"type": "NUMBER"}
                                }
                            },
                            "obligation_summary": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "level": {"type": "STRING", "enum": ["mandatory", "recommended", "optional"]},
                                        "total_rules": {"type": "NUMBER"},
                                        "passed": {"type": "NUMBER"},
                                        "failed": {"type": "NUMBER"}
                                    }
                                }
                            },
                            "violations": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "rule_path": {"type": "STRING"},
                                        "description": {"type": "STRING"},
                                        "severity": {"type": "STRING", "enum": ["low", "medium", "high"]},
                                        "obligation_level": {"type": "STRING", "enum": ["mandatory", "recommended", "optional"]}
                                    }
                                }
                            },
                            "skipped_rules": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "rule_path": {"type": "STRING"},
                                        "reason": {"type": "STRING"}
                                    }
                                }
                            },
                            "auto_fix_possible": {"type": "BOOLEAN"}
                        },
                        required=["compliance_score", "compliant", "compatibility_score", "violations", "auto_fix_possible", "scorecard", "obligation_summary"]
                    )
                )
            )
            if hasattr(response, 'parsed'):
                return response.parsed
            return response
        except Exception as e:
            return {"error": f"AI evaluation failed: {str(e)}"}

    async def analyze_compatibility(self, standard_json: Dict[str, Any], target_text: str) -> Dict[str, Any]:
        """
        Phase 2: Compatibility Analysis
        Scores how reasonable it is to apply a standard to a target document.
        Uses 5 weighted dimensions: doc type (30%), structure (25%), language (20%),
        compliance (15%), terminology (10%).
        """
        if not await self.is_available():
            return {"error": "AI Service not configured"}

        prompt = f"""
        You are a document compatibility assessor.
        You must be conservative and risk-aware.

        Compare the reference standard with the target document.

        Score compatibility (0-100) across these EXACT weighted dimensions:
        - document_type_score (weight 30%): How similar are the document types? (policy vs manual vs SOP vs training)
        - structural_similarity_score (weight 25%): Do they share similar section structures, hierarchy, and patterns?
        - language_model_score (weight 20%): Do they use the same language model? (must/should vs WARNING/CAUTION)
        - compliance_philosophy_score (weight 15%): Are their compliance approaches compatible? (audit vs operational)
        - terminology_overlap_score (weight 10%): How much shared vocabulary exists?

        Compute the total_score as the weighted sum:
        total = (doc_type * 0.30) + (structure * 0.25) + (language * 0.20) + (compliance * 0.15) + (terminology * 0.10)

        Classify risk:
        - total >= 75: "HIGH" (safe to apply)
        - total 40-74: "MEDIUM" (apply selectively with warnings)
        - total < 40: "LOW" (do NOT transform, report only)

        REFERENCE STANDARD (JSON):
        {str(standard_json)}

        TARGET DOCUMENT:
        {target_text[:200000]}
        """

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=types.Schema(
                        type="OBJECT",
                        properties={
                            "total_score": {"type": "NUMBER"},
                            "risk_classification": {"type": "STRING", "enum": ["HIGH", "MEDIUM", "LOW"]},
                            "dimensions": {
                                "type": "OBJECT",
                                "properties": {
                                    "document_type_score": {"type": "NUMBER"},
                                    "structural_similarity_score": {"type": "NUMBER"},
                                    "language_model_score": {"type": "NUMBER"},
                                    "compliance_philosophy_score": {"type": "NUMBER"},
                                    "terminology_overlap_score": {"type": "NUMBER"}
                                }
                            },
                            "target_document_type": {"type": "STRING"},
                            "reasoning": {"type": "STRING"}
                        },
                        required=["total_score", "risk_classification", "dimensions", "target_document_type", "reasoning"]
                    )
                )
            )
            if hasattr(response, 'parsed'):
                return response.parsed
            return response
        except Exception as e:
            return {"error": f"Compatibility analysis failed: {str(e)}"}

    async def select_rules(self, standard_json: Dict[str, Any], compatibility_score: float) -> Dict[str, Any]:
        """
        Phase 3: Rule Selection
        Categorizes rules into safe (always), conditional (if compatible), forbidden (never auto-apply).
        """
        if not await self.is_available():
            return {"error": "AI Service not configured"}

        prompt = f"""
        You are a compliance-safe rule selector.
        Never apply rules that could change meaning.

        Given a standard specification and a compatibility score of {compatibility_score}/100,
        categorize EVERY rule in the standard into one of three categories:

        🟢 SAFE rules (always allowed, never change meaning):
        - Section ordering
        - Heading hierarchy
        - Versioning metadata
        - Document identifiers
        - Formatting consistency

        🟡 CONDITIONAL rules (apply only if compatibility >= 40, warn the user):
        - Language normalization (must/should)
        - Compliance sections
        - Governance statements
        - Audit terminology

        🔴 FORBIDDEN rules (NEVER auto-apply, report only):
        - Domain-specific content
        - Legal obligations
        - Safety instructions
        - Engineering constraints
        - Training authority assignments

        For each rule, provide the rule_path, description, and a justification.

        STANDARD SPECIFICATION (JSON):
        {str(standard_json)}
        """

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=types.Schema(
                        type="OBJECT",
                        properties={
                            "safe_rules": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "rule_path": {"type": "STRING"},
                                        "description": {"type": "STRING"},
                                        "justification": {"type": "STRING"}
                                    }
                                }
                            },
                            "conditional_rules": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "rule_path": {"type": "STRING"},
                                        "description": {"type": "STRING"},
                                        "justification": {"type": "STRING"}
                                    }
                                }
                            },
                            "forbidden_rules": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "rule_path": {"type": "STRING"},
                                        "description": {"type": "STRING"},
                                        "justification": {"type": "STRING"}
                                    }
                                }
                            }
                        },
                        required=["safe_rules", "conditional_rules", "forbidden_rules"]
                    )
                )
            )
            if hasattr(response, 'parsed'):
                return response.parsed
            return response
        except Exception as e:
            return {"error": f"Rule selection failed: {str(e)}"}

    async def transform_document(self, doc_text: str, approved_rules: Dict[str, Any], competence_level: str = "general") -> Dict[str, Any]:
        """
        Phase 4: Gated Transformation with Deviation Accountability
        Only applies pre-approved rules. Preserves meaning at all costs.
        Returns structured JSON with the transformed text AND a deviation report.
        """
        if not await self.is_available():
            return {"transformed_text": "", "error": "AI Service not configured"}

        source_standard = approved_rules.get("source_standard", {})
        doc_type = source_standard.get("document_type", "other")
        
        tech_manual_instructions = ""
        if doc_type in ["manual", "specification"]:
            tech_manual_instructions = f"""
        TECHNICAL MANUAL OVERRIDE (CRITICAL REALISM INJECTION):
        Because this standard is a '{doc_type}', you must optimize for ENGINEERING REALISM, not just readability.
        You MUST inject the following specific traits:
        1. Engineering Density: Include numeric limits, torque values, temperatures, sizes, or material constraints where plausible.
        2. Tables: Present at least one set of step-by-step limits, specs, or troubleshooting data as a Markdown Table.
        3. Conditional Failure Modeling: Use phrasing like "If X occurs..." or "If leakage persists..." to model real-world consequences.
        4. Cross-Reference Synthesizer: Synthesize references frequently, e.g., "See Section X", "Refer to Figure 14", "As shown in Table 3".
        5. OEM Voice Calibration: Maintain a conservative, legal distancing tone (e.g., "Responsibility remains with the end user...").
        6. Competence Dial ({competence_level} Level):
           - operator: clear procedures, explain basics, focus on safe operation.
           - technician: skip obvious basics, focus on maintenance, disassembly, and specific risk points.
           - engineer: highly dense, jargon-heavy, assumes complete competence, focuses on parameters and root causes.
        7. Visual Realism: To emulate a real engineering manual, you MUST inject rich Markdown image placeholders for diagrams, schematics, and pictures where appropriate (e.g., `![System Diagram](https://placehold.co/600x400/1e293b/e2e8f0?text=System+Diagram)`).
        """

        prompt = f"""
        You are a policy-aware document transformation engine.
        Preserve meaning at all costs. You must be ACCOUNTABLE for every change.

        Apply ONLY the approved rules to the target document.

        CRITICAL CONSTRAINTS:
        1. Return the ENTIRE document text. Do NOT truncate or summarize. Use Markdown formatting.
        2. Do NOT introduce new obligations that don't exist in the original.
        3. Do NOT invent content — only restructure, reformat, or relabel (except for the technical realism parameters if specified below).
        4. Insert placeholders (e.g. "[TO BE ADDED]") where required sections are missing.
        5. MANDATORY: Images are the lifeblood of a technical manual. You MUST preserve ALL inline images precisely as they appear in the source. These look like `![alt](data:image...;base64,...)`. These strings are extremely long; you MUST NOT truncate, modify, or strip them. Every single `data:image` token must be carried over to the transformed document in its exact location.
        6. Do NOT upgrade MAY to SHOULD, or SHOULD to MUST. Obligation levels are FROZEN.
        {tech_manual_instructions}

        DEVIATION ACCOUNTABILITY:
        For EVERY change you make, you MUST log it as a deviation:
        - location: where in the document (e.g. "Section 3.2, paragraph 1")
        - original_text: the exact text before your change (short excerpt)
        - changed_to: what you changed it to
        - reason: WHY you made this change (reference the rule)
        - rule_reference: which approved rule triggered this change
        - severity: "cosmetic" (formatting only), "structural" (section reordering), or "semantic" (affects meaning)

        Also list items you explicitly CHOSE NOT TO CHANGE and why in preserved_items.
        Provide a brief change_summary describing the overall transformation.

        APPROVED RULES (JSON):
        {str(approved_rules)}

        DOCUMENT TO TRANSFORM:
        {doc_text[:200000]}
        """

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=types.Schema(
                        type="OBJECT",
                        properties={
                            "transformed_text": {"type": "STRING"},
                            "deviations": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "location": {"type": "STRING"},
                                        "original_text": {"type": "STRING"},
                                        "changed_to": {"type": "STRING"},
                                        "reason": {"type": "STRING"},
                                        "rule_reference": {"type": "STRING"},
                                        "severity": {"type": "STRING", "enum": ["cosmetic", "structural", "semantic"]}
                                    }
                                }
                            },
                            "preserved_items": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "change_summary": {"type": "STRING"}
                        },
                        required=["transformed_text", "deviations", "change_summary"]
                    )
                )
            )
            if hasattr(response, 'parsed'):
                result = response.parsed
            else:
                result = {"transformed_text": response.text, "deviations": [], "change_summary": "Transformation completed"}
            return result
        except Exception as e:
            return {"transformed_text": "", "deviations": [], "error": f"AI transformation failed: {str(e)}"}

ai_service = AIService()
