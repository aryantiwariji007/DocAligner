import io
from odf.opendocument import load
from odf import style, text, meta
from typing import Dict, Any, List

class ODFExtractionService:
    def extract_rules(self, file_content: bytes) -> Dict[str, Any]:
        """
        Parses an ODF file (bytes) and extracts structural and stylistic rules.
        """
        doc = load(io.BytesIO(file_content))
        
        rules = {
            "metadata": self._extract_metadata(doc),
            "styles": self._extract_styles(doc),
            "fonts": self._extract_fonts(doc),
            "namespaces": self._extract_namespaces(doc) # basic check
        }
        return rules

    def _extract_metadata(self, doc) -> Dict[str, str]:
        metadata = {}
        # Iterate over meta tags
        # Note: odfpy access to meta is somewhat direct if we look at doc.meta
        # But commonly we check child nodes of office:meta
        if doc.meta:
            for child in doc.meta.childNodes:
                if child.qname:
                    local_name = child.qname[1] if isinstance(child.qname, tuple) else child.tagName
                    # Simple text extraction
                    text_content = ""
                    for text_node in child.childNodes:
                        if text_node.nodeType == text_node.TEXT_NODE:
                            text_content += text_node.data
                    metadata[local_name] = text_content.strip()
        return metadata

    def _extract_styles(self, doc) -> Dict[str, Any]:
        extracted_styles = {}
        # Iterate over automatic and common styles
        # doc.styles (common identifiers), doc.automaticstyles
        
        for styles_node in [doc.styles, doc.automaticstyles]:
            if not styles_node:
                continue
            for s in styles_node.childNodes:
                if s.qname == (style.ns, 'style'):
                    style_name = s.getAttribute('name')
                    family = s.getAttribute('family')
                    parent = s.getAttribute('parent-style-name')
                    
                    properties = {}
                    # Extract properties (text-properties, paragraph-properties)
                    for prop in s.childNodes:
                        if prop.qname == (style.ns, 'text-properties'):
                            for k, v in prop.attributes.items():
                                properties[f"text:{k[1]}"] = v
                        elif prop.qname == (style.ns, 'paragraph-properties'):
                            for k, v in prop.attributes.items():
                                properties[f"paragraph:{k[1]}"] = v
                    
                    extracted_styles[style_name] = {
                        "family": family,
                        "parent": parent,
                        "properties": properties
                    }
        return extracted_styles

    def _extract_fonts(self, doc) -> List[str]:
        fonts = []
        if doc.fontfacedecls:
            for face in doc.fontfacedecls.childNodes:
                if face.qname == (style.ns, 'font-face'):
                     name = face.getAttribute('name')
                     if name:
                         fonts.append(name)
        return fonts
        
    def _extract_namespaces(self, doc) -> Dict[str, str]:
        # Just return known namespaces for validation
        return {k:v for k,v in doc.xmlns.items()}

odf_extractor = ODFExtractionService()
