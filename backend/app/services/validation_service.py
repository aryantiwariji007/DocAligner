from odf.opendocument import load
from odf import meta, style
import io
import zipfile
from typing import Dict, List, Any, Tuple
from backend.app.models import StandardVersion

class ValidationService:
    async def validate_document_async(self, file_content: bytes, standard_version: StandardVersion, filename: str) -> Dict[str, Any]:
        """
        Phase 2: Document Evaluation
        Deterministic validation + LLM-based compliance check.
        """
        # 1. Start with deterministic validation (fast)
        report = self.validate_document(file_content, standard_version)
        
        # 2. Augment with AI if available (Phase 2)
        try:
            from backend.app.services.ai_service import ai_service
            if ai_service.is_available():
                # Extract text for AI
                text = ""
                # Use the new factory method we added!
                from backend.app.services.rule_extraction_service import rule_extraction_factory
                text = rule_extraction_factory.extract_text(file_content, filename)

                if text:
                    ai_report = await ai_service.evaluate_compliance(text, standard_version.rules_json)
                    
                    # Merge Reports
                    # Phase 2 model: score + violations + fix options
                    if ai_report:
                        report["ai_evaluation"] = {
                            "compliance_score": ai_report.get("compliance_score", 0),
                            "compliant": ai_report.get("compliant", False),
                            "compatibility_score": ai_report.get("compatibility_score", 0),
                            "compatibility_warning": ai_report.get("compatibility_warning"),
                            "scorecard": ai_report.get("scorecard"),
                            "obligation_summary": ai_report.get("obligation_summary", []),
                            "violations": ai_report.get("violations", []),
                            "skipped_rules": ai_report.get("skipped_rules", []),
                            "auto_fix_possible": ai_report.get("auto_fix_possible", False)
                        }
                    
                    # If AI says non-compliant, override or append?
                    # Let's trust AI for "compliance rules" that deterministic code can't check.
                    if ai_report and ai_report.get("compliant") is False:
                        report["compliant"] = False
                        
                        # Add AI violations to main errors list
                        ai_violations = ai_report.get("violations", [])
                        for v in ai_violations:
                            desc = v.get("description", "Unknown violation")
                            rule_path = v.get("rule_path", "")
                            lvl = v.get("obligation_level", "mandatory")
                            report["errors"].append(f"[{lvl.upper()}] {desc} ({rule_path})")
                    
                    report["score"] = ai_report.get("compliance_score", 0) if ai_report else 0
                    report["fix_options"] = ai_report.get("auto_fix_possible", False) if ai_report else False
        except Exception as e:
            print(f"AI Validation failed: {e}")
            report["warnings"].append(f"AI-enhanced validation failed: {str(e)}")
            report["ai_evaluation"] = {"error": str(e)}

        return report

    def validate_document(self, file_content: bytes, standard_version: StandardVersion) -> Dict[str, Any]:
        """
        Validates a document against a standard version.
        Supports: ODF (Full), PDF (Basic), Word (Format Check).
        """
        report = {
            "compliant": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }

        # Identify Format
        is_zip = zipfile.is_zipfile(io.BytesIO(file_content))
        is_pdf = file_content.startswith(b"%PDF-")

        if is_pdf:
            report["details"]["format"] = "PDF"
            # Basic PDF validation (can be expanded with pypdf)
            report["warnings"].append("PDF documents only support metadata/format validation. Structural standards are skipped.")
            return report

        if is_zip:
            # Check if it's ODF or DOCX
            try:
                with zipfile.ZipFile(io.BytesIO(file_content)) as z:
                    # ODF has mimetype as first file
                    if "mimetype" in z.namelist():
                        mimetype = z.read("mimetype").decode("utf-8")
                        if "opendocument" in mimetype:
                            return self._validate_odf(file_content, standard_version, report)
                    
                    # Word (OOXML)
                    if "word/document.xml" in z.namelist():
                        report["details"]["format"] = "DOCX"
                        report["warnings"].append("Word documents (.docx) support macro detection but skip structural ODF standards.")
                        if self._has_macros_docx(file_content):
                            report["compliant"] = False
                            report["errors"].append("Macros detected in Word document.")
                        return report
            except:
                pass

        report["compliant"] = False
        report["errors"].append("Unsupported file format. Please upload ODF, PDF, or Word (.docx) files.")
        return report

    def _validate_odf(self, file_content: bytes, standard_version: StandardVersion, report: Dict[str, Any]) -> Dict[str, Any]:
        try:
            doc = load(io.BytesIO(file_content))
            report["details"]["format"] = "ODF"
        except Exception as e:
            report["compliant"] = False
            report["errors"].append(f"Invalid ODF file: {str(e)}")
            return report

        # Check version
        root = doc.topnode
        odf_version = root.getAttribute("version")
        if odf_version != "1.2":
            report["warnings"].append(f"Document version is '{odf_version}', expected '1.2'.")
            if odf_version != "1.2":
                report["compliant"] = False
                report["errors"].append(f"Strict ODF 1.2 compliance failed. Found version: {odf_version}")
        
        # 2. No Macros Allowed
        if self._has_macros(file_content):
            report["compliant"] = False
            report["errors"].append("Macros detected. Macros are strictly forbidden.")

        # 3. Metadata Validation
        # Rules from standard_version.rules_json.get('metadata', {})
        target_metadata = standard_version.rules_json.get("metadata", {})
        doc_metadata = self._extract_metadata(doc)
        
        for key, value in target_metadata.items():
            # If standard defines a metadata field, it MUST exist? 
            # Or must match value? 
            # "Metadata-driven enforcement" usually means required fields.
            if key not in doc_metadata:
                report["compliant"] = False
                report["errors"].append(f"Missing required metadata field: {key}")
            elif doc_metadata[key] != value:
                # Value mismatch - rigorous or just existence?
                # "Standards extracted from source document" implies template matching.
                # I'll warn on value mismatch but error on missing key.
                report["warnings"].append(f"Metadata mismatch for {key}. Expected '{value}', got '{doc_metadata[key]}'")

        # 4. Style & Heading Structure
        # Check if document uses styles not defined in standard? 
        # Or check if structure matches?
        # "Accessible document structure"
        # "Style and heading structure"
        # Implementation: Check if styles used in content.xml exist in standard rules.
        self._validate_styles(doc, standard_version.rules_json.get("styles", {}), report)

        return report

    def _has_macros(self, file_content: bytes) -> bool:
        """
        Check for presence of Basic/ or Scripts/ directories in ZIP.
        """
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as z:
                for name in z.namelist():
                    if name.startswith("Basic/") or name.startswith("Scripts/"):
                        return True
                    # manifest.xml check for script entries?
        except:
            pass # load() already passed, so zip should be valid
        return False

    def _extract_metadata(self, doc) -> Dict[str, str]:
        # Duplicate logic from extractor, maybe refactor common later
        metadata = {}
        if doc.meta:
            for child in doc.meta.childNodes:
                if child.qname:
                    local_name = child.qname[1] if isinstance(child.qname, tuple) else child.tagName
                    text_content = ""
                    for text_node in child.childNodes:
                        if text_node.nodeType == text_node.TEXT_NODE:
                            text_content += text_node.data
                    metadata[local_name] = text_content.strip()
        return metadata

    def _validate_styles(self, doc, allowed_styles: Dict[str, Any], report: Dict[str, Any]):
        """
        Validates that styles defined in the document match the allowed styles text-properties.
        """
        doc_styles = self._extract_styles_simple(doc)
        
        for style_name, rules in allowed_styles.items():
            # We enforce that if the document HAS this style, it must match.
            # If standard has "Heading 1" and doc doesn't, that's fine (unless mandatory? assuming no).
            # But if doc has "Heading 1", it must match rules.
            
            if style_name in doc_styles:
                doc_style = doc_styles[style_name]
                # Compare text properties
                rule_props = rules.get("properties", {})
                doc_props = doc_style.get("properties", {})
                
                for prop_key, prop_val in rule_props.items():
                    # Only check text properties for now, e.g. "text:font-name"
                    if prop_key in doc_props:
                        if doc_props[prop_key] != prop_val:
                            report["warnings"].append(
                                f"Style '{style_name}' mismatch: {prop_key} expected '{prop_val}', got '{doc_props[prop_key]}'"
                            )
                    # If prop is missing in doc style but present in rule? 
                    # Maybe it inherits? Complex. Warning for now.
                    # else:
                    #    report["warnings"].append(f"Style '{style_name}' missing property {prop_key}")

    def _extract_styles_simple(self, doc) -> Dict[str, Any]:
        extracted = {}
        # Simple extractor for validation comparisons
        # Using odfpy's styles and automaticstyles
        for styles_node in [doc.styles, doc.automaticstyles]:
            if not styles_node: continue
            for s in styles_node.childNodes:
                if s.qname == (style.ns, 'style'):
                    name = s.getAttribute('name')
                    properties = {}
                    for prop in s.childNodes:
                        if prop.qname == (style.ns, 'text-properties'):
                            for k, v in prop.attributes.items():
                                properties[f"text:{k[1]}"] = v
                    extracted[name] = {"properties": properties}
        return extracted

    def _has_macros_docx(self, file_content: bytes) -> bool:
        """
        Check for vbaProject.bin or other common macro indicators in DOCX.
        """
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as z:
                for name in z.namelist():
                    if "vbaProject" in name or name.endswith(".vba") or "macros" in name.lower():
                        return True
        except:
            pass
        return False

validation_service = ValidationService()
