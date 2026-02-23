import asyncio
import os
from backend.app.services.rule_extraction_service import rule_extraction_factory

def test():
    # Find a PDF file in the documents bucket (simulated via file system if possible)
    # Actually, I'll just look for any PDF in the workspace
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.lower().endswith(".pdf"):
                path = os.path.join(root, file)
                print(f"Testing extraction on: {path}")
                with open(path, "rb") as f:
                    content = f.read()
                text = rule_extraction_factory.extract_text(content, file)
                print(f"Extracted length: {len(text)}")
                print(f"Preview: {text[:200]}...")
                return

if __name__ == "__main__":
    test()
