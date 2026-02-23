try:
    import fitz
    print("FITZ_OK")
    print(f"VERSION:{fitz.version}")
except Exception as e:
    print(f"FITZ_ERROR:{e}")
except ImportError as e:
    print(f"FITZ_IMPORT_ERROR:{e}")
