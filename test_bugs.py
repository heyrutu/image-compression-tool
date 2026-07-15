"""
Test script to find bugs in the image compression tool
"""
import os
from PIL import Image
from app import app, db, User, ImageRecord, compress_image, allowed_file
import tempfile

# Create app context
with app.app_context():
    db.create_all()
    
    # Test 1: Create a test BMP image and try to compress it
    print("=" * 60)
    print("TEST 1: BMP Image Compression (Testing for PIl optimize bug)")
    print("=" * 60)
    
    # Create a simple test BMP image
    test_img = Image.new('RGB', (100, 100), color='red')
    test_bmp_path = 'test_image.bmp'
    test_img.save(test_bmp_path)
    
    # Try to compress it
    try:
        with open(test_bmp_path, 'rb') as f:
            from werkzeug.datastructures import FileStorage
            file_storage = FileStorage(
                stream=f,
                filename='test_image.bmp',
                content_type='image/bmp'
            )
            stored_filename, original_size, compressed_size, fmt = compress_image(file_storage, 75, False)
            print(f"✓ BMP compression successful")
            print(f"  Original: {original_size} bytes")
            print(f"  Compressed: {compressed_size} bytes")
            print(f"  Format: {fmt}")
    except Exception as e:
        print(f"✗ BMP compression FAILED with error:")
        print(f"  {type(e).__name__}: {e}")
    finally:
        if os.path.exists(test_bmp_path):
            os.remove(test_bmp_path)
    
    # Test 2: Test allowed_file function with various extensions
    print("\n" + "=" * 60)
    print("TEST 2: File Type Validation")
    print("=" * 60)
    test_files = [
        'image.jpg',
        'image.jpeg',
        'image.png',
        'image.webp',
        'image.bmp',
        'image.gif',
        'image.svg',
        'document.pdf',
        'noextension'
    ]
    
    for filename in test_files:
        result = allowed_file(filename)
        status = "✓ ALLOWED" if result else "✗ BLOCKED"
        print(f"  {filename:20s} - {status}")
    
    # Test 3: Test human_size function
    print("\n" + "=" * 60)
    print("TEST 3: Human Size Formatter")
    print("=" * 60)
    from app import human_size
    test_sizes = [
        100,
        1024,
        1024 * 1024,
        1024 * 1024 * 1024,
        1024 * 1024 * 1024 * 1024,
        1024 * 1024 * 1024 * 1024 * 10
    ]
    
    for size in test_sizes:
        formatted = human_size(size)
        print(f"  {size:20d} bytes -> {formatted}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
