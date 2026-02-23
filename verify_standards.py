
import asyncio
import httpx
import json
import os
import sys

# Configuration
API_URL = "http://localhost:8000/api/v1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

async def test_standards_intelligence():
    async with httpx.AsyncClient() as client:
        # 1. Create a Standard
        print("\n[Step 1] Creating Standard...")
        try:
            std_resp = await client.post(f"{API_URL}/standards/", json={
                "name": "Test Standard V2",
                "description": "Verification Standard"
            })
            print(f"Status: {std_resp.status_code}")
            if std_resp.status_code != 200:
                print(f"Error: {std_resp.text}")
                return
            standard_id = std_resp.json()["id"]
            print(f"Success! Standard ID: {standard_id}")
        except Exception as e:
            print(f"Failed to create standard: {e}")
            return

        # 2. Upload a Reference Document (to be promoted)
        print("\n[Step 2] Uploading Reference Document...")
        # Create a dummy file
        ref_path = os.path.join(BASE_DIR, "ref_doc.txt")
        with open(ref_path, "wb") as f:
            f.write(b"This is a policy document. MUST use Title Case for headings. Should include version number.")
            
        try:
            with open(ref_path, "rb") as f:
                files = {'file': ('ref_doc.txt', f, 'text/plain')}
                doc_resp = await client.post(f"{API_URL}/documents/upload/", files=files)
            print(f"Status: {doc_resp.status_code}")
            if doc_resp.status_code != 200:
                print(f"Error: {doc_resp.text}")
                return
            ref_doc_id = doc_resp.json()["id"]
            print(f"Success! ref_doc_id: {ref_doc_id}")
        except Exception as e:
            print(f"Failed to upload ref doc: {e}")
            return

        # 3. Promote Document to Standard Version (This triggers Extraction Phase 1)
        print("\n[Step 3] Promoting Document (AI Extraction)...")
        # Increase timeout for AI
        promote_resp = await client.post(f"{API_URL}/standards/{standard_id}/versions/promote/{ref_doc_id}", timeout=60.0)
        print(f"Status: {promote_resp.status_code}")
        
        version_data = {}
        if promote_resp.status_code == 200:
            version_data = promote_resp.json()
            print("Extracted Rules JSON (Snippet):")
            print(json.dumps(version_data.get("rules_json", {}), indent=2)[:500] + "...")
        else:
            print(f"Error: {promote_resp.text}")
            return

        # 4. Upload a Test Document (to be validated)
        print("\n[Step 4] Uploading Test Document...")
        test_path = os.path.join(BASE_DIR, "test_doc.txt")
        with open(test_path, "wb") as f:
            f.write(b"this is a bad document. no version number.")
            
        try:
            with open(test_path, "rb") as f:
                files_test = {'file': ('test_doc.txt', f, 'text/plain')}
                test_doc_resp = await client.post(f"{API_URL}/documents/upload/", files=files_test)
            test_doc_id = test_doc_resp.json()["id"]
            print(f"Success! test_doc_id: {test_doc_id}")
        except Exception as e:
             print(f"Failed to upload test doc: {e}")
             return

        # 5. Apply Standard (Simulate Assignment)
        print("\n[Step 5] Applying Standard & Triggering Validation...")
        apply_resp = await client.post(f"{API_URL}/standards/{standard_id}/apply/document/{test_doc_id}")
        print(f"Status: {apply_resp.status_code}")

        # 6. Validate Document (Triggers Phase 2 Compliance)
        print("\n[Step 6] Polling for Validation Report...")
        for i in range(10):
            await asyncio.sleep(2) 
            val_resp = await client.get(f"{API_URL}/documents/{test_doc_id}/validation")
            data = val_resp.json()
            status = data.get('status')
            print(f"Attempt {i+1}: Status={status}")
            
            if status == "non_compliant" or status == "compliant":
                print("Compliance Report Found!")
                print(json.dumps(data.get('report', {}), indent=2)[:500] + "...")
                break
        else:
            print("Timeout waiting for validation.")

        # 7. Auto-Fix Document (Phase 3 Transformation)
        print("\n[Step 7] Auto-Fixing Document...")
        try:
            fix_resp = await client.post(f"{API_URL}/documents/{test_doc_id}/fix", timeout=60.0)
            print(f"Status: {fix_resp.status_code}")
            if fix_resp.status_code == 200:
                print("--- FIXED CONTENT START ---")
                print(fix_resp.json().get("fixed_content"))
                print("--- FIXED CONTENT END ---")
            else:
                print(f"Error: {fix_resp.text}")
        except Exception as e:
            print(f"Fix failed: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_standards_intelligence())
